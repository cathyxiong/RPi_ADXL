from i2clibraries import i2c_adxl345
from time import *

from datetime import datetime
import time

import os
import random
import argparse
import sys

import multiprocessing
from multiprocessing import Process, Queue

from configparser import ConfigParser
from collections import deque

# plumbum used for uploading via ssh SCP (must be downloaded via pip)
import plumbum

# Declare ADXL345 class from adxl345 library

myADXL = i2c_adxl345.i2c_adxl345(1)
	
piID = "RPi_Unassigned"

# Testing

# Interval controls how often we retrieve axes (seconds)
interval = 0.1

# Declare counters and counterError
counter = 0
counterError = 0
counterMax = 0
counterMaxTime = 0

# Declare list to store data from accelerometer
dataList = []

# Declare calibration values (x,y,z)
x_fix = 0
y_fix = 0
z_fix = 0
calibrationValues = [x_fix, y_fix, z_fix]

# Declare threshold values (for checking significance)
# Value in g
x_threshold = 0.4
y_threshold = 0.4
z_threshold = 0.4
significanceThresholds = [x_threshold, y_threshold, z_threshold]
checkForSignificance = True

# Declare axis information (for reference)
# Up/Down, North/South, East/West
axisOrientationInfo = ["z", "x", "y"]

# Folder to store files
dataFolder = "dataFolder/"

# Queue for files yet to be uploaded
uploadQueue = Queue()

class significanceBuffer():
	# timeNotSignificant is the stopwatch for how long we've gone so far without anything significant
	# bufferTime is how many seconds we should buffer
	# all in seconds
	
	def __init__(self):
		self.bufferList = []
		self.bufferTime = 3
		self.timeNotSig = 0
		self.sleepTimeMax = 3
		self.sleeping = False
		
		self.x_threshold = 0.1
		self.y_threshold = 0.1
		self.z_threshold = 0.1
	
	def processData(self, dataList, interval):
		if self.checkListForSignificance(dataList):
			# if recent packet is significant, wake up!
			self.timeNotSig = 0
			
			if self.sleeping:
				print("-> Waking up! Activity detected @ " + str(datetime.now()))
				self.sleeping = False
				return (self.bufferList + dataList)
			else:
				return dataList
			
		else: # if not significant:
			# if sleeping, do buffer tasks
			if self.sleeping:
				self.addToBufferList(dataList, interval)
				return dataList
			else: # if not sleeping, track and check if we should put to sleep
				self.timeNotSig += (len(dataList)*interval)
				if self.timeNotSig > self.sleepTimeMax:
					print("-> Sleeping due to inactivity @ " + str(datetime.now()))
					self.sleeping = True
				return dataList
				
	def addToBufferList(self, dataList, interval):
		# Append dataList to bufferList
		self.bufferList += dataList
		
		# if bufferLists exceeds our bufferTime, remove
		# from the leftmost on the list instead of clearing list
		if (len(self.bufferList)*interval > self.bufferTime):
			self.bufferList = self.bufferList[len(dataList):]

	def setThresholds(self, x, y, z):
		self.threshold_x = x
		self.threshold_y = y
		self.threshold_z = z
	
	def getXYZtFromPacket(packet):
		x = packet[0]
		y = packet[1]
		z = packet[2]
		time = packet[3]
		return (x, y, z, time)
		
	def checkListForSignificance(self, dataList):
		for packet in dataList:
			(x, y, z, time) = getXYZtFromPacket(packet)
			if x > self.x_threshold or x < (self.x_threshold * -1):
				return True
			if y > self.y_threshold or y < (self.y_threshold * -1):
				return True
			if z > self.z_threshold or z < (self.z_threshold * -1):
				return True
		
		return False
	



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
		
def clearScreen():
	os.system('clear')

def calibrateAxesValues(x, y, z):
	x += calibrationValues[0]
	y += calibrationValues[1]
	z += calibrationValues[2]
	return (x, y, z)

def getCalibrationOffsets ():
	# Collect data for a certain amount of time to get averages (for subtraction)

	counterCalibrate = 0
	counterCalibrateMax = 100
	calibrateList = []
	calibrateValues = []
	calibrateLoop = True
	
	x_average = 0
	y_average = 0
	z_average = 0
	
	while counterCalibrate <= counterCalibrateMax:
		counterCalibrate += 1
		(accel_x, accel_y, accel_z) = myADXL.getAxes()
		calibrateValues = [accel_x, accel_y, accel_z]
		calibrateList.append(calibrateValues)
		
	for	dataValues in calibrateList:
		x_average += dataValues[0]
		y_average += dataValues[1]
		z_average += dataValues[2]
	
	x_fix = (x_average / len(calibrateList))*-1
	y_fix = (y_average / len(calibrateList))*-1
	z_fix = (z_average / len(calibrateList))*-1
	calibrationValues = [x_fix, y_fix, z_fix]
	
	return calibrationValues

def getXYZtFromPacket(packet):
	x = packet[0]
	y = packet[1]
	z = packet[2]
	time = packet[3]
	return (x, y, z, time)

def getData():
	(x, y, z) = myADXL.getAxes()
	time = datetime.now()
	(x, y, z) = calibrateAxesValues(x, y, z)
	axesPacket = [x, y, z, str(time)]
	return axesPacket

def getRPiSettings(settingsLocation = "RPi_settings.ini"):
	settings = ConfigParser()
	settings.read(settingsLocation)
	
	settingsDict = {}
	mainSettings = dict(settings.items("Main"))
	uploadSettings = dict(settings.items("Upload"))
	
	# Combine the above into one settings dict
	settingsDict = mainSettings.copy()
	settingsDict.update(uploadSettings)
	
	# Convert the following variables listed below into float/bools
	floatSettings = ["adxl_interval", "save_interval", "x_thresh", "y_thresh", "z_thresh"]
	booleanSettings = ["checkforsignificance", "uploading"]
	
	for setting in settingsDict:
		if setting in floatSettings:
			settingsDict[setting] = float(settingsDict[setting])
		if setting in booleanSettings:
			settingsDict[setting] = (settingsDict[setting] == "True")
		
	#settingsDict["counterMax"] = (settingsDict["save_interval"]*60)/settingsDict["adxl_interval"]
	settingsDict["piID"] = settings["RPi"]["piID"]
	settingsDict["countermax"] = (settingsDict["save_interval"])/settingsDict["adxl_interval"]
	
	return settingsDict


def applyRPiSettings(settings):
	# Translate to normal variables for readability
	# It pains me to use these global variables
	global piID, interval, counterMaxTime, counterMax, checkForSignificance
	global significanceThresholds, axisOrientationInfo, dataFolder
	global uploadUser, uploadHost, uploadDirectory, uploadInterval, uploading
	
	piID = settings["piID"]
	interval = settings["adxl_interval"]
	counterMaxTime = settings["save_interval"]
	counterMax = settings["countermax"]
	checkForSignificance = settings["checkforsignificance"]
	significanceThresholds = [settings["x_thresh"], settings["y_thresh"], settings["z_thresh"]]
	axisOrientationInfo = [settings["up_orient"], settings["north_orient"], settings["east_orient"]]
	dataFolder = settings["datafolder"]
	piID = settings["piID"]
	dataFolder = settings["datafolder"]
	uploadUser = settings["uploaduser"]
	uploadHost = settings["uploadhost"]
	uploadDirectory = settings["uploaddirectory"]
	uploadInterval = settings["uploadinterval"]
	uploading = settings["uploading"]
	
def printSettings(title):
	# This DOES NOT print whatever is in the settings dict
	# This is for printing the actual variables currently being used by the program
	# to make sure that the user is fully aware what values are ACTUALLY being used
	
	print ("\n######### " + title + " #########")
	print ("RPi ID: " + piID)
	print ("Interval: " + str(interval))
	print ("Counts per file: " + str(counterMax) + " - approx: " + str(counterMaxTime) + " seconds")
	print ("Checking for Significance - " + str(checkForSignificance))
	print ("Significance Thresholds - " + str(significanceThresholds))
	print ("Saving to - " + dataFolder)
	print ("Axis Orientation (UP/DOWN, NORTH/SOUTH, EAST/WEST): " + str(axisOrientationInfo))
	print("\n######### UPLOAD SETTINGS")
	if (uploading):
		print("Uploading to: " + uploadUser + "@" + uploadHost)
		print("Uploading every (default): " + str(uploadInterval))
		print("Remote data folder: " + uploadDirectory)
	else:
		print("NOT UPLOADING")
	
	
	
def strConvertAxes (x,y,z):
	return (str(x),str(y),str(z))
	
def writeToDisk(dataList, uploadQueue):
	# Append date to filename
	fileDate = datetime.now().strftime("[%Y-%m-%d_%H-%M-%S]")
	
	# Open data file
	mainDataFile = open(dataFolder + piID + '_data_' + fileDate, 'w')
	
	# Generate header string
	headerString = ('Pi_ID: ' + piID
					+ '\nSample rate: ' + str(interval)
					+ '\nSamples: ' + str(len(dataList))
					+ '\nLost: ' + str(counterError)
					+ '\nOrientation (U/D, N/S, E/W): ' + str(axisOrientationInfo) + '\n')
	
	# Write header into text file
	mainDataFile.write(headerString)
	
	# Write data line by line into text file
	for packet in dataList:
		(x, y, z, time) = getXYZtFromPacket(packet)
		(x,y,z) = strConvertAxes(x,y,z)
		mainDataFile.write(x + " " + y + " " + z + " " + str(time) + "\n")
	
	# Write "end" to bottom of file to mark that file has been fully written/uploaded
	mainDataFile.write("end")
	
	# Close mainDataFile
	mainDataFile.close()
	
	# Enter log that data was successfully written
	logString = ('[FW] Wrote @ ' + str(datetime.now())
				+ ' | Lost: ' + str(counterError))

	print(logString)
	
	# Don't bother uploading log files anymore
	# Add file that's been finished written to uploadqueue
	uploadQueue.put((dataFolder + piID + '_data_' + fileDate))
	
def userInputDialog(settings):
	while True:
		clearScreen()
		applyRPiSettings(settings)
		print ("######### RPi Online Smart Building Monitoring #########")
		print ("Written by Lui Villarias")
		
		printSettings("DEFAULT mainADXL SETTINGS")
		
		if (checkUserAnswer(input("\n>> Use these values? (y\\n): "))):
			break
		
		# Ask for data frequency
		settings["adxl_interval"] = float(input("\n>> Enter interval (s): "))
		
		# Ask for save interval
		settings["save_interval"] = float(input("\n>> Approximate save interval (minutes): "))
		settings["countermax"] = (settings["save_interval"]) / settings["adxl_interval"] # convert to counts
		#settings["counterMax"] = (settings["save_interval"] * 60) / settings["adxl_interval"] # convert to counts
		
		# Ask if significance thresholds will be used
		settings["checkforsignificance"] = checkUserAnswer(input("\n>> Save only significant data? (y\\n): "))
		
		settings["uploading"] = checkUserAnswer(input("\n>> Uploading to remote host (internet)? (y\\n): "))
		
		applyRPiSettings(settings)
		
	return settings

def uploadTheQueue(uploadQueue, uploadUser, uploadHost, uploadDirectory, remoteDestination, uploaderID):
	print("Uploader [" + uploaderID + "] started")
	
	while True:
		# get() will wait for new files to be added to the list by
		# fileWriter threads
		dataFile = uploadQueue.get()
		# Copy file through SCP
		#print("Attempting to upload - " + dataFile)
		
		while True:
			try:
				localFile = plumbum.local.path(dataFile)
				plumbum.path.utils.copy(localFile, remoteDestination)
				print("[U" + uploaderID + "] - " + dataFile + " uploaded")
				break
			except:
				pass
				print("[U" + uploaderID + "] - " + dataFile + " FAILED")
					

def fetchDataList(interval, counterMax):
	counter = 0
	dataList = []
	
	while counter < counterMax:
		dataList.append(getData())
		counter += 1
		sleep(interval)
		
	return dataList

def startThread_FileWriter(dataList, uploadQueue):
	thread_FileWriter = Process(name="FileWriter", target=writeToDisk, args=(dataList, uploadQueue,))
	thread_FileWriter.daemon = True
	thread_FileWriter.start()
	
def startThread_Uploader(uploadQueue, uploadUser, uploadHost, uploadDirectory,remoteDestination, uploaderID):
	thread_Uploader = Process(name="Uploader", target=uploadTheQueue, args=(uploadQueue, uploadUser, uploadHost, uploadDirectory,remoteDestination, uploaderID,))
	thread_Uploader.daemon = True
	thread_Uploader.start()

####################################################################################	
#### MAIN PROGRAM STARTS HERE ######################################################

clearScreen()

# Grab external args if we're skipping input
# For example, running in shell: "python3 mainADXL.py -s" will skip input
skipInput = checkUserSkip()
	
####### Retrieve settings.ini values
settings = getRPiSettings()
applyRPiSettings(settings)

####### CALIBRATION
# Get current values from resting ADXL345, average, and use to "calibrate"
calibrationValues = getCalibrationOffsets()
clearScreen()	
#######

####### INPUT INITIAL VALUES
if skipInput == False:
	settings = userInputDialog(settings)
	clearScreen()
#######

####### INITIATE MAIN PROGRAM LOOP
# Do not clear screen here - leave a summary log per file written
	
printSettings("RPi_ADXL RUNNING")
print ("\nStarted @ " + str(datetime.now()) + "\n\n")

##### INITIATE UPLOAD THREAD and UPLOAD QUEUE
# Declare queue that can be shared between processes
uploadQueue = Queue()

# Initiate upload workers
if uploading:
	print("Connecting to SCP Session - " + uploadUser + "@" + uploadHost)
	t1 = datetime.now()
	SCPSession = plumbum.machines.SshMachine(uploadHost, user=uploadUser, keyfile="/home/pi/.ssh/upload")
	print("Connected in ", end="")
	print(datetime.now()-t1)
	remoteDestination = SCPSession.path(uploadDirectory + piID + "/")
	
	# We will create n upload workers
	# So that we can upload n files simultaneously if needed
	uploaderWorkerAmount = 10
	for i in range(0, uploaderWorkerAmount):
		startThread_Uploader(uploadQueue, uploadUser, uploadHost, uploadDirectory, remoteDestination, str(i))
	
	#SCPSession.close()

# Start significance buffer class
significanceBuffer = significanceBuffer()

# Using "try" to ignore count losses from I/O errors
while True:
	try:	
		# Grab axes values from ADXL and add to dataList
		dataList = fetchDataList(interval, counterMax)
		
		if checkForSignificance:
			dataList = significanceBuffer.processData(dataList, interval)
		
		# If we're not sleeping, write the file. Otherwise sleep.
		if (not significanceBuffer.sleeping) or (not checkForSignificance):
			startThread_FileWriter(dataList, uploadQueue)
		
		counterError = 0
	except IOError:
		counterError += 1
		
SCPSession.close()