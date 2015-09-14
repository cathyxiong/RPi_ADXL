#########
# Upload script to be run simulatneously with mainADXL.py
# (for now on a separate session)
#########

from collections import deque
from configparser import ConfigParser
import os
import sys
from time import *
from datetime import datetime

# glob used for easy file searching in directory
from glob import glob

# plumbum used for uploading via ssh SCP (must be downloaded via pip)
import plumbum

# declare uploadQueue
uploadQueue = deque()

# declare lists for files sent before & log for filewriting
dataSentHistoryList = []
logList = []
	
def getRPiSettings(settingsLocation = "RPi_settings.ini"):
	settings = ConfigParser()
	settings.read(settingsLocation)
	
	settingsDict = {}
	settingsDict["piID"] = settings["RPi"]["piID"]
	settingsDict["uploadUser"] = settings["Upload"]["uploadUser"]
	settingsDict["uploadHost"] = settings["Upload"]["uploadHost"]
	settingsDict["uploadDirectory"] = settings["Upload"]["uploadDirectory"]
	settingsDict["dataFolder"] = settings["Upload"]["dataFolder"]
	
	return settingsDict


def printUploadSettings(settings):
	print("[UPLOADADXL SETTINGS]")
	print("piID: " + settings["piID"])
	print("Uploading to: " + settings["uploadUser"] + "@" + settings["uploadHost"])
	print("Remote data folder: " + settings["uploadDirectory"])
	print("Local data folder: " + settings["dataFolder"])
	print("\n")
		

def log(description, save = True, printScreen = True):
	if (save):
		logList.append((str(datetime.now()) + " - ") + description)
	
	if (printScreen):
		print(description)
	return True


def writeLog():
	fileName = dataFolder + piID + "_upload_log"
	logFile = open(fileName, 'a')
	
	for line in logList:
		logFile.write(line + "\n")
		
	logFile.write("\n======= SCPuploadADXL.py reinitiated =======")
	
	logFile.close()
	return True


def scanFolder(dataFolder):
	uploadQueue = deque()
	
	dataFileNameList = glob(dataFolder + piID + "_data*")
	log("New files found: " + str(len(dataFileNameList)))
	
	print("Populating the upload queue...")	
	for dataFileName in dataFileNameList:
		if ((dataFileName in dataSentHistoryList) == False):
			uploadQueue.append(dataFileName)
			
	print(str(len(uploadQueue)) + " added to the queue from " 
		+ str(len(dataFileNameList))
		+ " files found")
		
	return uploadQueue
	
	
def addToSentHistoryList(dataFileName):
	dataSentHistoryList.append(dataFileName)

	
def connectToSCPHost(remote, username):
	# Locate SSH private key for uploading to server
	sshLocation = "/home/pi/.ssh/upload"
	#sshLocation = "/home/pi/.ssh/DOPrivateKeyOSSH"
	
	log("Connecting to SCP Session - " + username + "@" + remote)
	try:
		SCPSession = plumbum.machines.SshMachine(remote, user=username, keyfile=sshLocation)
		log("Connected to SCP Session")
		return SCPSession
	except Exception as error:
		log("!!! - ERROR - connectToSCPHost() - failed to connect")
		log("	   ERROR WAS: " + str(error))
		return -1
	

def disconnectFromSCPHost(SCPSession):
	return SCPSession.close()
	
	
def uploadFile(fileName, SCPSession, location):
	log("Uploading " + fileName)
	try:
		localFile = plumbum.local.path(fileName)
		remoteDestination = SCPSession.path(location + piID + "/")
		plumbum.path.utils.copy(localFile, remoteDestination)
	except Exception as error:
		log("!!! ERROR - uploadFile()- failed to up: " + fileName)
		log("	 ERROR WAS: " + str(error))
	
	addToSentHistoryList(fileName)
	
	
def uploadTheQueue(uploadQueue, SCPSession, uploadDirectory):
	# Upload entire queue
	log("Uploading [" + str(len(uploadQueue)) + "] data files in queue...")
	log("Uploading to remote server in " + uploadDirectory)
	while uploadQueue:
		uploadFile(uploadQueue.popleft(), SCPSession, location=uploadDirectory)

		
def clearScreen():
	os.system('clear')		

	
######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################
clearScreen()

# Retrieve all settings for upload
settings = getRPiSettings()

# Assign settings to variables
piID = settings["piID"]
dataFolder = settings["dataFolder"]
uploadUser = settings["uploadUser"]
uploadHost = settings["uploadHost"]
uploadDirectory = settings["uploadDirectory"]

# Print out settings
printUploadSettings(settings)
input("Press [ENTER] to continue . . .")

# Ask how often we should try to upload
interval = float(input("\nHow often to check and upload (in minutes): ")) * 60
		
# First scan the folder for files and grab files
while True:
	clearScreen()
	logList = []
	
	print("\n######### uploadADXL (SCP) running #########\n")
	printUploadSettings(settings)
	print("Uploading every " + str(interval/60) + " minutes")
	
	# Scan folder for new files to send out
	print("Scanning folder and populating upload queue...")
	uploadQueue = scanFolder(dataFolder)
	
	# Connect to remote host
	SCPSession = connectToSCPHost(uploadHost, uploadUser)
	
	# Do NOT upload if connection failed to resolve
	if (SCPSession != -1):
		if (uploadQueue):
			print("\nUploading new files in queue...")
			uploadTheQueue(uploadQueue, SCPSession, uploadDirectory)
			log("Upload complete")
		else:
			print("\nQueue empty!")

		

		# Upload data and upload log file (to update)
		uploadFile((dataFolder + piID + "_log"), SCPSession, uploadDirectory)
		
		# Dump log to file
		writeLog()

		# Upload log file online
		uploadFile((dataFolder + piID + "_upload_log"), SCPSession, uploadDirectory)
		SCPSession = disconnectFromSCPHost(SCPSession)

	print("Slept @ " + str(datetime.now()))
	print("\n\nSleeping until next upload interval...")
	
	sleep(interval)


