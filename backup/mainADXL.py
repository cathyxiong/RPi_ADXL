from i2clibraries import i2c_adxl345
from time import *

from datetime import datetime
import os

# Declare ADXL345 class from adxl345 library
myADXL = i2c_adxl345.i2c_adxl345(1)

# Interval controls how often we retrieve axes (seconds)
interval = 0.1

# Declare counters and counter_error
counter = 0
counterFile = 0
maxCounterFile = 90000
counter_error = 0
maxCounterToWrite = 36000
displayLoop = True
display = True

filenumber = 1

# Declare list to store data from accelerometer
dataList = []

# Declare calibration Fixes
x_fix = 0
y_fix = 0
z_fix = 0

def strConvertAxes (x,y,z):
	return (str(x),str(y),str(z))

	
def printAxes (x,y,z):
	(x,y,z) = strConvertAxes(x,y,z)

	print("\n\n[ADXL345]")
	print("X: " + x + "g")
	print("Y: " + y + "g")
	print("Z: " + z + "g")

def trackCounter():
	global counter
	global counter_error
	global counterFile

	counter += 1
	counterFile += 1

	print("COUNT: " + str(counter))
	print("LOST COUNTS: " + str(counter_error))

def addToList(dataList, x, y, z, time):
	(x,y,z) = strConvertAxes(x,y,z)
	#axesPacket = [x,y,z]
	dataList.append(x)
	dataList.append(y)
	dataList.append(z)
	dataList.append(time)
	# ";" denotes end of sample
	dataList.append(";")
	return dataList


#def checkDataUseful(dataList, interval, counter):

	
	
	
	
	
def writeToDisk(dataList, interval):
	# n is a counter for dataList
	n = 0
	
	# i is a counter for filename
	global filenumber
	global counter
	global counter_error
	
	if filenumber < 10:
		filenumberWrite = '0' + str(filenumber)
	else:
		filenumberWrite = filenumber
	
	mainDataFile = open('ADXLData/adxl_datafile' + str(filenumberWrite), 'w')
	mainDataFile.write("ADXL345 Data File\nSample Rate: " + str(interval) + "\nSamples: " + str(len(dataList)/5) + "\n")
	
	for item in dataList:
		n += 1
		if item != ";":
			mainDataFile.write(item)
			if n < 4:
				mainDataFile.write(" ")
		elif item == ";":
			mainDataFile.write("\n")
			n = 0
	mainDataFile.close()
	filenumber += 1
			

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
	z_fix = ((z_average / len(calibrateList))*-1)+1
	
	return (x_fix, y_fix, z_fix)
	
def calibrateAxesValues(x, y, z):
	global x_fix
	global y_fix
	global z_fix

	x += x_fix
	y += y_fix
	z += z_fix
	return (x,y,z)
		

def mainDisplayADXL (interval, write, display):
	# Interval is in seconds, and controls how often we read and print from ADXL
	# Use "try/except" to prevent IOError from interrupting display loop
	# We will increment an error counter to track loss
	global counter
	global counterFile
	global displayLoop
	global dataList
	
	try:
		os.system("clear")
		trackCounter()
		
		(accel_x, accel_y, accel_z) = myADXL.getAxes()
		(accel_x, accel_y, accel_z) = calibrateAxesValues(accel_x, accel_y, accel_z)
		
		if display:
			printAxes(accel_x,accel_y,accel_z)
			print(str(datetime.now()))
			print("\nRetrieving every " + str(interval) + " seconds")
			
		if write:
			dataList = addToList(dataList, accel_x, accel_y, accel_z, str(datetime.now()))
			if counterFile >= maxCounterFile:
				writeToDisk(dataList, interval)
				dataList = []
				counterFile = 0
			if counter >= maxCounterToWrite:
				displayLoop = False
			
	except IOError:
		global counter_error
		counter_error += 1

	sleep(interval)
	



	
###################################

# Get current values from resting ADXL345, average, and use to "calibrate"
(x_fix, y_fix, z_fix) = getCalibrationOffsets()


interval = float(input("\nEnter interval: "))
maxCounterToWrite = (float(input("\nHow long for: (m) "))*60)/interval
maxCounterFile = (float(input("\nSave file every: (m) "))*60)/interval

print ("Interval: " + str(interval))
print ("Duration: " + str(maxCounterToWrite))
print ("Save Intervals; " + str(maxCounterFile))


display = float(input("\nDisplay? (0, 1): "))
if display == 0:
	display = False
else:
	display = True

## MAIN LOOP 

myADXL.setScale(4)

while displayLoop:
	mainDisplayADXL(interval, True, display)
