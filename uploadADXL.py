#########
# Upload script to be run simulatneously with mainADXL.py
# (for now on a separate session)
#########
import ftplib
from glob import glob
from collections import deque
import os
from time import *
from datetime import datetime

uploadQueue = deque()

#dataFileNameList = []
dataSentHistoryList = []

FTPSession = 0

dataFolder = "ADXLData/"
piID = "RPi_Lui"

interval = 0.5 # in minutes


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
	
def connectFTP():
	# NOTE THAT THIS IS HIGHLY INSECURE DUE TO PLAIN TEXT PASSWORD
	# CONSIDER USING SFTP FOR REAL WORLD APPLICATION
	global FTPSession
	
	ip = '192.168.0.100'
	port = 45557
	user = "lui"
	pw = "quincy"
	
	print("Attempting to connect to local FTP server...")
	FTPSession = ftplib.FTP()
	FTPSession.connect(ip, port, 5)
	FTPSession.login(user, pw)

def disconnectFTP():
	global FTPSession
	FTPSession.quit()
	print("Stopping connection with FTP server...")
		
def uploadDataFile(fileName):
	global FTPSession
	
	file = open(fileName, 'rb')
	FTPSession.storbinary(('STOR ' + (fileName.split("/")[1])), file)
	print(fileName + " uploaded")
	addToSentHistoryList(fileName)
	file.close()
	
def uploadLogFile():
	global FTPSession
	global dataFolder, piID
	
	fileName = (piID + "_log")
	
	logFile = open((dataFolder + fileName), 'rb')
	FTPSession.storbinary(('STOR ' + fileName), logFile)
	
	print(fileName + " uploaded")
	
	logFile.close()
	
def uploadTheQueue(uploadQueue):
	connectFTP()
	
	while uploadQueue:
		uploadDataFile(uploadQueue.popleft())
		
	uploadLogFile()
	disconnectFTP()

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
		try:
			uploadTheQueue(uploadQueue)
		except:
			print("\n\n!!! Error while uploading")
	else:
		print("\nQueue empty!")

	print("\n\nSleeping until next upload interval...")
	print("Slept @ " + str(datetime.now()))
	print("Interval: " + str(interval/60) + " minutes")
	
	sleep(interval)


