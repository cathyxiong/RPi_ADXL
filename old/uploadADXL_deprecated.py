#########
# Upload script to be run simulatneously with mainADXL.py
# (for now on a separate session)
#########

from collections import deque
from configparser import ConfigParser
import os
import sys
import argparse
from time import *
from datetime import datetime

# glob used for easy file searching in directory
from glob import glob

# plumbum used for uploading via ssh SCP (must be downloaded via pip)
import plumbum

# DECLARE ALL VARIABLES FOR NEATNESS ####################!!!!!!!!!!!!!!!!!#################

# Declare uploadQueue
uploadQueue = deque()

# Declare lists for files sent before & log for filewriting
dataSentHistoryList = []
logList = []

# Declare variables for neatness
piID = ""
dataFolder = ""
uploadUser = ""
uploadHost = ""
uploadDirectory = ""
uploadInterval = 5
	
def getRPiSettings(settingsLocation = "RPi_settings.ini"):
	settings = ConfigParser()
	settings.read(settingsLocation)

	settingsDict = {}
	settingsDict["piID"] = settings["RPi"]["piID"]
	
	settingsToGrabStrings = ["uploadUser", "uploadHost", "uploadDirectory", "dataFolder"]
	settingsToGrabNumbers = ["uploadInterval"]
	
	for type in settingsToGrabStrings:
		settingsDict[type] = settings["Upload"][type]
	
	for type in settingsToGrabNumbers:
		settingsDict[type] = float(settings["Upload"][type])
	
	return settingsDict

def applyRPiSettings(settings):
	global piID, dataFolder
	global uploadUser, uploadHost, uploadDirectory
	global uploadInterval
	
	piID = settings["piID"]
	dataFolder = settings["dataFolder"]
	uploadUser = settings["uploadUser"]
	uploadHost = settings["uploadHost"]
	uploadDirectory = settings["uploadDirectory"]	
	uploadInterval = settings["uploadInterval"]*60

def printUploadSettings(settings):
	print("[UPLOADADXL SETTINGS]")
	print("piID: " + piID)
	print("Uploading to: " + uploadUser + "@" + uploadHost)
	print("Uploading every (default): " + str(uploadInterval/60))
	print("Remote data folder: " + uploadDirectory)
	print("Local data folder: " + dataFolder)
	print("\n")

def checkUserAnswer(input):
	yes = ["yes", "ye", "y", "1", "ok"]
	
	if (input.lower() in yes):
		return True
	else:
		return False	

def checkUserSkip():
	# We use Argument Parser to read if script was run with any shell arguments
	# This way we can easily start scripts and skip all user input
	argParser = argparse.ArgumentParser()
	argParser.add_argument("-s", "--skipinput", action ="store_true", 
						help="Skip user input")
	args = argParser.parse_args()
	if args.skipinput:
		return True
	else:
		return False
		
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
		
	logFile.write("## uploadADXL.py reinitiated @ " + str(datetime.now()) + " ##\n")
	
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
	
	
def uploadFile(fileName, SCPSession, uploadDirectory):
	log("Uploading " + fileName)
	try:
		localFile = plumbum.local.path(fileName)
		remoteDestination = SCPSession.path(uploadDirectory + piID + "/")
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
		uploadFile(uploadQueue.popleft(), SCPSession, uploadDirectory)

		
def clearScreen():
	os.system('clear')

	
######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################
clearScreen()

# Grab external args if we're skipping input
# For example, running in shell: "python3 mainADXL.py -s" will skip input
skipInput = checkUserSkip()

# Retrieve all settings for upload
settings = getRPiSettings()

# Assign settings to variables
applyRPiSettings(settings)

# Print out settings
if skipInput == False:
	printUploadSettings(settings)
	qString = "Use this upload interval? [" + str(uploadInterval/60) + " minutes] (y\\n) "
	if checkUserAnswer(input(qString)) == False:
		uploadInterval = float(input("\nHow often to check and upload (in minutes): ")) * 60
	
# First scan the folder for files and grab files
while True:
	clearScreen()
	logList = []
	
	print("\n######### uploadADXL (SCP) running #########\n")
	printUploadSettings(settings)
	print("Uploading every " + str(uploadInterval/60) + " minutes")
	
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
	
	sleep(uploadInterval)


