from i2clibraries import i2c_adxl345
from time import *

from datetime import datetime
import time

import os
import random


# Declare ADXL345 class from adxl345 library
myADXL = i2c_adxl345.i2c_adxl345(1)
piID = "RPi_Lui"

# Interval controls how often we retrieve axes (seconds)
interval = 0.1

# Declare counters and counterError
counter = 0
counterMax = 0
counterMaxTime = 0

fileNumber = 1

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
checkingForSignificance = True

def strConvertAxes (x,y,z):
	return (str(x),str(y),str(z))


def getXYZtFromPacket(packet):
	x = packet[0]
	y = packet[1]
	z = packet[2]
	time = packet[3]
	return (x, y, z, time)

# before writing to disk, check entire list if anything significant happened. Otherwise, delete.

def checkListForSignificance(dataList):
	global significanceThresholds
	x_threshold = significanceThresholds[0]
	y_threshold = significanceThresholds[1]
	z_threshold = significanceThresholds[2]
	
	for packet in dataList:
		(x, y, z, time) = getXYZtFromPacket(packet)
		if x > x_threshold or x < (x_threshold * -1):
			return True
		if y > y_threshold or y < (y_threshold * -1):
			return True
		if z > z_threshold or z < (z_threshold * -1):
			return True
	return False

	
def generateDataID():
	ID = ""
	randomNumber = 0
	digits = 16

	# Generate 5 separate numbers and attach
	for n in range (0, digits):
		randomNumber = random.randint(0,9)
		ID += str(randomNumber)
	return ID
	
def writeToDisk(dataList, interval, checking, piID):
	global fileNumber
	# Measure writing speed:
	# timeStart = time.time()
	
	fileUniqueID = generateDataID()
	headerString = ('Pi_ID: ' + piID
					+ '\nData_ID: ' + fileUniqueID
					+ '\nSample rate: ' + str(interval)
					+ '\nSamples: ' + str(len(dataList)) + '\n')

	#testing!
	# Format file numbering for 01, 02 ... 09 etc
	if fileNumber < 10:
		fileNumberWrite = '0' + str(fileNumber)
	else:
		fileNumberWrite = fileNumber
	
	# Open log file
	logDataFile = open('ADXLData/' + piID + '_log', 'a')
	
	# If prompted to check and list has NO significant values, record that no data was significant
	if checking and checkListForSignificance(dataList) == False:
		logString = ('No significant data @ ' + str(datetime.now()))
		logDataFile.write(logString + '\n')
		print(logString)
		
		logDataFile.close()
		return
	
	# Open data file
	mainDataFile = open('ADXLData/'+ piID + '_data_' + str(fileNumberWrite), 'w')
	fileNumber += 1
	
	# Write header into text file
	mainDataFile.write(headerString)
	
	# Write data line by line into text file
	for packet in dataList:
		(x, y, z, time) = getXYZtFromPacket(packet)
		(x,y,z) = strConvertAxes(x,y,z)
		mainDataFile.write(x + " " + y + " " + z + " " + str(time) + "\n")
		
	mainDataFile.close()
	
	logString = ('[' + fileNumberWrite + '] File written @ ' + str(datetime.now()) + ' | ID: ' + fileUniqueID)
	logDataFile.write(logString + '\n')
	print(logString)
	
	logDataFile.close()
	
	# Print write speed
	#print('File written @ ' + str(datetime.now()) + ' approx ' + str(time.time() - timeStart) + 's')
	


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
	
	
def calibrateAxesValues(x, y, z):
	global calibrationValues
	
	x += calibrationValues[0]
	y += calibrationValues[1]
	z += calibrationValues[2]
	return (x, y, z)


def getData():
	(x, y, z) = myADXL.getAxes()
	time = str(datetime.now())
	(x, y, z) = calibrateAxesValues(x, y, z)
	axesPacket = [x, y, z, time]
	return axesPacket
	
def addToList(dataList, axesPacket):
	dataList.append(axesPacket)
	return dataList
	
def readAndAddToList(dataList, calibrationValues):
	(x, y, z) = calibrateAxesValues(x, y, z, calibrationValues)
	axesPacket = [x, y, z, timeRead]
	dataList.append(axesPacket)
	return dataList
		
def checkInputAnswer(input):
	if float(input) == 0:
		return False
	else:
		return True
		
def clearScreen():
	os.system("clear")

def mainUserInput():
	global interval, counterMaxTime, counterMax, checkingForSignificance
	
	while True:
		print ("######### RPi Online Smart Building Monitoring #########")
		print ("Written by Lui Villarias")
		
		if (checkInputAnswer(input("Use default testing values? (0,1) ")) == False):
		
			interval = float(input("\nEnter interval (s): "))
			counterMaxTime = float(input("\nApproximate save interval (minutes): "))
			counterMax = (counterMaxTime * 60) / interval # convert to counts
			checkingForSignificance = checkInputAnswer(input("\nSave only significant data? (0,1): "))
		
		else:
		
			interval = 0.01
			counterMaxTime = 0.05
			counterMax = (counterMaxTime * 60) / interval
			checkingForSignificance = True
		
			# DISPLAY INPUT RESPONSE
		clearScreen()
		printSettings("USER INPUT SUMMARY")

		if (checkInputAnswer(input("\nIS THIS CORRECT? (0,1) "))):
			break
		
		
		
		clearScreen()

def printSettings(title):
	global interval, counterMaxTime, counterMax
	global checkingForSignificance, significanceThresholds
	global piID
	
	print ("\n######### " + title + " #########")
	print ("RPi ID: " + piID)
	print ("Interval: " + str(interval))
	print ("Counts per file: " + str(counterMax) + " - approx: " + str(counterMaxTime) + " minutes")
	print ("Checking for Significance - " + str(checkingForSignificance))
	print ("Significance Thresholds - " + str(significanceThresholds))


		
def mainDisplayADXL():
	global counter, counterMax, fileNumber
	global dataList
	global significanceThresholds, checkingForSignificance
	global calibrationValues
	global piID
	
	printSettings("RPi_ADXL RUNNING")
	print ("\nStarted @ " + str(datetime.now()) + "\n\n")
	
	# Using "try" to ignore count losses from I/O errors
	while True:
		try:	
			# Grab axes values from ADXL and add to dataList
			dataList = addToList(dataList, getData())
			counter += 1
			
			if counter > counterMax:
				writeToDisk(dataList, interval, checkingForSignificance, piID)
				dataList = []
				counter = 0
			
		except IOError:
			# Ignore IOERROR
			pointless = 0
		sleep(interval)
	
## TO DO
# write switch axes function

	
###################################

####### CALIBRATION
# Get current values from resting ADXL345, average, and use to "calibrate"
calibrationValues = getCalibrationOffsets()
clearScreen()	
#######

####### INPUT INITIAL VALUES
mainUserInput()
clearScreen()
#######

# Do not clear screen here - leave a summary log per file written
mainDisplayADXL()
