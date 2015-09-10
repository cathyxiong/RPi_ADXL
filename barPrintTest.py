from i2clibraries import i2c_adxl345
from time import *
import os

while True:
	try:
		adxl345 = i2c_adxl345.i2c_adxl345(1)
		break
	except IOError:
		print("error")


x_fix = 0
y_fix = 0
z_fix = 0

def printBar(axis, axisValue):
	print(axis + ": ", end="")
	for n in range (0, abs(int(round(axisValue*60,0)))):
		print("=", end="")
	print("\n")
	
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
		#getAxes
		(accel_x, accel_y, accel_z) = adxl345.getAxes()
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

(x_fix, y_fix, z_fix) = getCalibrationOffsets()
	
while True:
	try:
		(x,y,z) = adxl345.getAxes()
		(x,y,z) = calibrateAxesValues(x,y,z)
		print(x)
		print(y)
		print(z)
		printBar("x", x)
		printBar("y", y)
		printBar("z", z)
		sleep(0.02)
		os.system("clear")
	except IOError:
		print("")
