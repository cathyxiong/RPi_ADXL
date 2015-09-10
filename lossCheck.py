from i2clibraries import i2c_adxl345
from time import *

from datetime import datetime
import os

# Declare ADXL345 class from adxl345 library
myADXL = i2c_adxl345.i2c_adxl345(1)

# Interval controls how often we retrieve axes (seconds)
interval = 0.02

# Declare counters and counter_error
counter = 0
counter_error = 0
maxCounterToWrite = 200
displayLoop = True
lossesStreak = 0
lossesStreakRecord = 0

# Declare list to store data from accelerometer
dataList = []

lossStreakList =[]

def strConvertAxes (x,y,z):
	return (str(x),str(y),str(z))
	
def printAxes (x,y,z):
	(x,y,z) = strConvertAxes(x,y,z)

	print("\n[ADXL345]")
	print("X: " + x + "g")
	print("Y: " + y + "g")
	print("Z: " + z + "g")

def trackCounter():
	global counter
	global counter_error

	global lossesStreak
	global lossesStreakRecord
	
	counter += 1

	print("COUNT: " + str(counter))
	print("LOST: " + str(counter_error) + " (" + str(round((counter_error / (counter+counter_error))*100,1)) + ")%")
	print("LOST STRK/REC: " + str(lossesStreak) + " " + str(lossesStreakRecord))
	

def mainDisplayADXL (interval, write, dataList):
	# Interval is in seconds, and controls how often we read and print from ADXL
	# Use "try/except" to prevent IOError from interrupting display loop
	# We will increment an error counter to track loss
	global counter
	global displayLoop
	global lossesStreak
	global lossesStreakRecord
	global lossStreakList
	
	try:
		trackCounter()
		print(lossStreakList)
		
		(accel_x, accel_y, accel_z) = myADXL.getAxes()
		print("Interval: " + str(interval))
		
		if lossesStreak > 1:
			lossStreakList.append(lossesStreak)
			if len(lossStreakList) >= 5:
				lossStreakList.pop(0)
			
		lossesStreak = 0
		
	except IOError:
		print ("IOERROR thrown")
		global counter_error
		lossesStreak += 1
		counter_error += 1

	sleep(interval)
	

## MAIN LOOP 
while displayLoop:
	os.system("clear")
	mainDisplayADXL(interval, True, dataList)
	
	if counter >= 100:
		counter = 0
		counter_error = 0
