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
dataFolder = "ADXLData/"
#dataFileNameList = []
dataSentHistoryList = []
piID = "RPi_Lui"
FTPSession = 0


interval = 0.5 # in minutes


def scanFolder(dataFolder):
	global dataSentHistoryList
	uploadQueue = deque()
	
	dataFileNameList = glob(dataFolder + piID + "_data*")
	print ("\nFiles found: " + str(dataFileNameList) + "\n")
	
	print("Adding to queue...")
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
	
	
	FTPSession = ftplib.FTP()
	FTPSession.connect(ip, port)
	FTPSession.login(user, pw)

def disconnectFTP():
	global FTPSession
	FTPSession.quit()
		
def uploadFile(fileName):
	global FTPSession
	
	file = open(fileName, 'rb')
	FTPSession.storbinary(('STOR ' + (fileName.split("/")[1])), file)
	print(fileName + " uploaded")
	addToSentHistoryList(fileName)
	file.close()

def uploadTheQueue(uploadQueue):
	connectFTP()
	
	while uploadQueue:
		uploadFile(uploadQueue.popleft())
		
	disconnectFTP()

def clearScreen():
	os.system('clear')		

#### MAIN PROGRAM STARTS HERE
# convert interval to seconds
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
		uploadTheQueue(uploadQueue)
	else:
		print("\nQueue empty!")

	print("\n\nSleeping until next upload interval...")
	print("Slept @ " + str(datetime.now()))
	print("Interval: " + str(interval/60) + " minutes")
	
	sleep(interval)


