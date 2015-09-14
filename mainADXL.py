from i2clibraries import i2c_adxl345
from time import *

from datetime import datetime
import time

import os
import random

from configparser import ConfigParser
from collections import deque

# DECLARE ALL VARIABLES FOR NEATNESS ####################!!!!!!!!!!!!!!!!!#################

# Declare ADXL345 class from adxl345 library
try:
	myADXL = i2c_adxl345.i2c_adxl345(1)
	generateZeroData = False
except:
	myADXL = 0
	generateZeroData = True
	
piID = "RPi_Unassigned"

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

def checkUserAnswer(input):
	yes = ["yes", "ye", "y", "1", "ok"]
	
	if (input.lower() in yes):
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

def generateDataID():
	ID = ""
	randomNumber = 0
	digits = 16

	# Generate 5 separate numbers and attach
	for n in range (0, digits):
		randomNumber = random.randint(0,9)
		ID += str(randomNumber)
	return ID

def getData():
	(x, y, z) = myADXL.getAxes()
	time = str(datetime.now())
	(x, y, z) = calibrateAxesValues(x, y, z)
	axesPacket = [x, y, z, time]
	return axesPacket

def getRPiSettings(settingsLocation = "RPi_settings.ini"):
	settings = ConfigParser()
	settings.read(settingsLocation)
	
	settingsDict = {}
	settingsDict["piID"] = settings["RPi"]["piID"]
	
	# Distinguish between strings/numbres/boolean so we can convert them
	settingsToGrabNumbers = ["adxl_interval", "save_interval", "x_thresh", "y_thresh", "z_thresh"]
	settingsToGrabStrings = ["up_orient", "east_orient", "north_orient"]
	settingsToGrabBoolean = ["checkForSignificance"]
	
	for type in settingsToGrabStrings:
		settingsDict[type] = settings["Main"][type]
		
	for type in settingsToGrabNumbers:
		settingsDict[type] = float(settings["Main"][type])
		
	for type in settingsToGrabBoolean:
		settingsDict[type] = (settings["Main"][type] == "True")
	
	settingsDict["counterMax"] = (settingsDict["save_interval"]*60)/settingsDict["adxl_interval"]

	return settingsDict

def applyRPiSettings(settings):
	# Translate to normal variables for readability
	# It pains me to use these global variables
	global piID, interval, counterMaxTime, counterMax, checkForSignificance
	global significanceThresholds, axisOrientationInfo
	
	piID = settings["piID"]
	interval = settings["adxl_interval"]
	counterMaxTime = settings["save_interval"]
	counterMax = (counterMaxTime*60)/interval
	checkForSignificance = settings["checkForSignificance"]
	significanceThresholds = [settings["x_thresh"], settings["y_thresh"], settings["z_thresh"]]
	axisOrientationInfo = [settings["up_orient"], settings["north_orient"], settings["east_orient"]]
	
def printSettings(title):
	# This DOES NOT print whatever is in the settings dict
	# This is for printing the actual variables currently being used by the program
	# to make sure that the user is fully aware what values are ACTUALLY being used
	
	print ("\n######### " + title + " #########")
	print ("RPi ID: " + piID)
	print ("Interval: " + str(interval))
	print ("Counts per file: " + str(counterMax) + " - approx: " + str(counterMaxTime) + " minutes")
	print ("Checking for Significance - " + str(checkForSignificance))
	print ("Significance Thresholds - " + str(significanceThresholds))
	print ("Axis Orientation (UP/DOWN, NORTH/SOUTH, EAST/WEST): " + str(axisOrientationInfo))

	# Print a warning if we're generating zero data
	if generateZeroData:
		print("!! - WARNING - NOT GENERATING ACTUAL ADXL DATA !!!")
	
def strConvertAxes (x,y,z):
	return (str(x),str(y),str(z))
	
def writeToDisk(dataList, settings):
	global counter, counterError
	global axisOrientationInfo	

	# Append date to filename
	fileDate = datetime.now().strftime("[%Y-%m-%d_%H-%M-%S]")
	
	# Open log file
	logDataFile = open('ADXLData/' + piID + '_log', 'a')
	
	# If prompted to check and list has NO significant values, record that no data was significant
	if checkForSignificance and (checkListForSignificance(dataList) == False):
		logString = ('No significant data @ ' + str(datetime.now())
					+ ' | Lost: ' + str(counterError))
		logDataFile.write(logString + '\n')
		print(logString)
		
		logDataFile.close()
		return
	
	# Open data file
	mainDataFile = open('ADXLData/'+ piID + '_data_' + fileDate, 'w')
	
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
	
	# Close mainDataFile
	mainDataFile.close()
	
	# Enter log that data was successfully written
	logString = ('File written @ ' + str(datetime.now())
				+ ' | Lost: ' + str(counterError))
				
	logDataFile.write(logString + '\n')
	print(logString)
	logDataFile.close()
	
def userInputDialog(settings):
	while True:
		clearScreen()
		print ("######### RPi Online Smart Building Monitoring #########")
		print ("Written by Lui Villarias")
		
		printSettings("DEFAULT mainADXL SETTINGS")
		
		if (checkUserAnswer(input("\n>> Use these values? (y\\n): "))):
			break
		
		# Ask for data frequency
		settings["adxl_interval"] = float(input("\n>> Enter interval (s): "))
		
		# Ask for save interval
		settings["save_interval"] = float(input("\n>> Approximate save interval (minutes): "))
		settings["counterMax"] = (settings["save_interval"] * 60) / settings["adxl_interval"] # convert to counts
		
		# Ask if significance thresholds will be used
		settings["checkForSignificance"] = checkUserAnswer(input("\n>> Save only significant data? (y\\n): "))
		
		applyRPiSettings(settings)
		
	return settings
	
	
	
## TO DO
# write switch axes function


####################################################################################	
#### MAIN PROGRAM STARTS HERE ######################################################

####### Retrieve settings.ini values
settings = getRPiSettings()
applyRPiSettings(settings)

####### CALIBRATION
# Get current values from resting ADXL345, average, and use to "calibrate"
calibrationValues = getCalibrationOffsets()
clearScreen()	
#######

####### INPUT INITIAL VALUES
settings = userInputDialog(settings)
clearScreen()
#######

####### INITIATE MAIN PROGRAM LOOP
# Do not clear screen here - leave a summary log per file written
printSettings("RPi_ADXL RUNNING")
print ("\nStarted @ " + str(datetime.now()) + "\n\n")

# Using "try" to ignore count losses from I/O errors
while True:
	try:	
		# Grab axes values from ADXL and add to dataList
		if (generateZeroData == False):
			dataList.append(getData())
		else:
			dataList.append([0,0,0,str(datetime.now())])
			
		counter += 1
		
		if counter > counterMax:
			writeToDisk(dataList, settings)
			dataList = []
			counter = 0
			counterError = 0
		
	except IOError:
		counterError += 1
		
	
sleep(interval)