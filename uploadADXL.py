#########
# Upload script to be run simulatneously with mainADXL.py
# (for now on a separate session)
#########

from collections import deque
import os
import sys
from time import *
from datetime import datetime

# glob used for easy file searching in directory
from glob import glob

# plumbum used for uploading via ssh SCP (must be downloaded via pip)
import plumbum

uploadQueue = deque()

dataSentHistoryList = []
logList = []

def getRPiSettings(getList = ["piID", "uploadUser", "uploadHost", "dataFolder"]):
	file = open("ADXLsettings.txt", "r")
	settings = {}
	
	# Retrieve Pi ID
	# Strip used to remove \n from line
	for line in file:
		for type in getList:
			if ((type in line) and (type in getList)):
				settings[type] = (line.split("=")[1]).strip()
				
	return settings

def printUploadSettings(settings):
	print("[UPLOADADXL SETTINGS]")
	print("piID: " + settings["piID"])
	print("Uploading to: " + settings["uploadUser"] + "@" + settings["uploadHost"])
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
	sshLocation = "/home/pi/.ssh/DOPrivateKeyOSSH"
	
	log("Connecting to SCP Session - " + username + "@" + remote)
	try:
		SCPSession = plumbum.machines.SshMachine(remote, user=username, keyfile=sshLocation)
		log("Connected to SCP Session")
		return SCPSession
	except:
		log("!!! - ERROR - connectToSCPHost() - failed to connect")
		return -1
	

def disconnectFromSCPHost(SCPSession):
	return SCPSession.close()
	
def uploadFile(fileName, SCPSession, location = "/var/www/104.236.141.183/public_html/RPi_ADXL_Storage/"):
	# Default location set to public_html folder on remote server - for index view
	# location = "/root/RPi_ADXL_Storage/"
	log("Uploading " + fileName)
	try:
		localFile = plumbum.local.path(fileName)
		remoteDestination = SCPSession.path(location + piID + "/")
		plumbum.path.utils.copy(localFile, remoteDestination)
	except:
		log("!!! - ERROR - uploadFile() - failed to upload " + fileName)
	
	addToSentHistoryList(fileName)
	
def uploadTheQueue(uploadQueue, SCPSession):
	# Upload entire queue
	log("Uploading [" + str(len(uploadQueue)) + "] data files in queue...")
	while uploadQueue:
		uploadFile(uploadQueue.popleft(), SCPSession)

def clearScreen():
	os.system('clear')		

######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################
clearScreen()

# Retrieve all settings for upload
settings = getRPiSettings()

piID = settings["piID"]
dataFolder = settings["dataFolder"]
uploadUser = settings["uploadUser"]
uploadHost = settings["uploadHost"]

# Print out settings
printUploadSettings(settings)
input("Press [ENTER] to continue . . .")

# Ask how often we should try to upload
interval = float(input("\nHow often to check and upload (in minutes): ")) * 60
		
# First scan the folder for files and grab files
while True:
	clearScreen()
	print("\n######### uploadADXL (SCP) running #########\n")
	printUploadSettings(settings)
	print("Uploading every " + str(interval) + " minutes")
	
	# Scan folder for new files to send out
	print("Scanning folder and populating upload queue...")
	uploadQueue = scanFolder(dataFolder)
	
	# Connect to remote host
	SCPSession = connectToSCPHost(uploadHost, uploadUser)
	
	# Only attempt any upload if connection was established
	if (SCPSession != -1):
		# If queue has contents, upload them
		if (uploadQueue):
			print("\nUploading new files in queue...")
			# Upload the queue of data files and then upload data log
			uploadTheQueue(uploadQueue, SCPSession)
			
		else:
			print("\nQueue empty!")

		writeLog()
		
		# Upload data log file (to update)
		uploadFile("ADXLData/" + piID + "_log", SCPSession)
		uploadFile("ADXLData/" + piID + "_upload_log", SCPSession)
		log("Upload complete")	
		SCPSession = disconnectFromSCPHost(SCPSession)

	print("Slept @ " + str(datetime.now()))
	print("\n\nSleeping until next upload interval...")
	
	sleep(interval)


