#########
# Upload script to be run simulatneously with mainADXL.py
# (for now on a separate session)
#########

from collections import deque
import os
from time import *
from datetime import datetime

# glob used for easy file searching in directory
from glob import glob

# plumbum used for uploading via ssh SCP (must be downloaded via pip)
import plumbum


dataSentHistoryList = []
uploadQueue = deque()
dataFolder = "ADXLData/"
piID = "RPi_Lui"
logList = []

interval = 0.5 # in minutes

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
		
	logFile.write("\n")
	
	logFile.close()
	return True


def scanFolder(dataFolder):
	uploadQueue = deque()
	
	dataFileNameList = glob(dataFolder + piID + "_data*")
	log("New files found: " + str(len(dataFileNameList)))
	
	print("Populating queue...")	
	for dataFileName in dataFileNameList:
		if ((dataFileName in dataSentHistoryList) == False):
			uploadQueue.append(dataFileName)
			log(dataFileName + " added to upload queue")
	return uploadQueue
	
def addToSentHistoryList(dataFileName):
	dataSentHistoryList.append(dataFileName)

def connectToSCPHost(username, remote):
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
	
def uploadFile(fileName, SCPSession, location = "~/sftp"):
	log("Uploading " + fileName)
	try:
		localFile = plumbum.local.path(fileName)
		remoteDestination = SCPSession.path(location)
		plumbum.path.utils.copy(localFile, remoteDestination)
	except:
		log("ERROR - Failure uploading file")
	
	addToSentHistoryList(fileName)
	
def uploadTheQueue(uploadQueue, SCPSession):
	# Upload entire queue
	log("Uploading [" + str(len(uploadQueue)) + "] data files in queue...")
	while uploadQueue:
		uploadFile(uploadQueue.popleft(), SCPSession)

def clearScreen():
	os.system('clear')		

	
#### MAIN PROGRAM STARTS HERE
clearScreen()

# Ask how often we should try to upload
interval = float(input("How often to check and upload (in minutes): ") * 60)
		
# First scan the folder for files and grab files
while True:
	clearScreen()

	print ("\n######### uploadADXL (SCP) running #########\n")
	
	# Scan folder for new files to send out
	print("Scanning folder and populating upload queue...")
	uploadQueue = scanFolder(dataFolder)
	
	SCPSession = connectToSCPHost("root", "114.236.141.183")
	# "104.236.141.183"
	
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
		uploadFile("ADXLData/RPi_Lui_log", SCPSession)
		uploadFile("ADXLData/RPi_Lui_upload_log", SCPSession)
		SCPSession = disconnectFromSCPHost(SCPSession)

	print("\n\nSleeping until next upload interval...")
	print("Slept @ " + str(datetime.now()))
	print("Interval: " + str(interval/60) + " minutes")
	
	sleep(interval)


