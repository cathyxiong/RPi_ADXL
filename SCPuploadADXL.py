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


uploadQueue = deque()

#dataFileNameList = []
dataSentHistoryList = []

dataFolder = "ADXLData/"
piID = "RPi_Lui"

interval = 0.5 # in minutes

SCPSession = 0

def scanFolder(dataFolder):
	global dataSentHistoryList
	uploadQueue = deque()
	
	dataFileNameList = glob(dataFolder + piID + "_data*")
	print ("\nFiles found: " + str(len(dataFileNameList)) + "\n")
	
	print("Populating queue...")	
	for dataFileName in dataFileNameList:
		if ((dataFileName in dataSentHistoryList) == False):
			uploadQueue.append(dataFileName)
			print(dataFileName + " added to upload queue")
	return uploadQueue
	
def addToSentHistoryList(dataFileName):
	global dataSentHistoryList
	dataSentHistoryList.append(dataFileName)

def connectToSCPHost(username, remote):
	print("Connecting to SCP Session - " + username + "@" + remote)
	try:
		SCPSession = plumbum.machines.SshMachine(remote, user=username, keyfile="/home/pi/.ssh/DOPrivateKeyOSSH")
		print("CONNECTED to SCP Session\n")
		return SCPSession
	except:
		print("!!! ERROR - Unable to connect to SCP Session !!!")
		return -1
	

def disconnectFromSCPHost(SCPSession):
	SCPSession.close()
	
def uploadFile(fileName, SCPSession, location = "~/sftp"):
	print("Uploading " + fileName)
	try:
		localFile = plumbum.local.path(fileName)
		remoteDestination = SCPSession.path(location)
		plumbum.path.utils.copy(localFile, remoteDestination)
	except:
		print("!!! ERROR - Failure uploading file")
	
	addToSentHistoryList(fileName)
	
def uploadTheQueue(uploadQueue, SCPSession):
	print("Uploading [" + str(len(uploadQueue)) + "] data files in queue...")
	while uploadQueue:
		uploadFile(uploadQueue.popleft(), SCPSession)
		
	uploadFile("ADXLData/RPi_Lui_log", SCPSession)

def clearScreen():
	os.system('clear')		

	
#### MAIN PROGRAM STARTS HERE
clearScreen()

# convert interval to seconds
interval = float(input("How often to check and upload (in minutes): "))
interval = interval * 60
		
# First scan the folder for files and grab files
while True:
	clearScreen()

	print ("\n######### uploadADXL running #########\n")
	
	# Scan folder for new files to send out
	print("Scanning folder and populating upload queue...")
	uploadQueue = scanFolder(dataFolder)
	
	
	# If queue has contents, upload them
	if (uploadQueue):
		print("\nUploading new files in queue...")
		SCPSession = connectToSCPHost("root", "104.236.141.183")
		if (SCPSession != -1):
			uploadTheQueue(uploadQueue, SCPSession)
			disconnectFromSCPHost(SCPSession)
	else:
		print("\nQueue empty!")

	print("\n\nSleeping until next upload interval...")
	print("Slept @ " + str(datetime.now()))
	print("Interval: " + str(interval/60) + " minutes")
	
	sleep(interval)


