#########
# PLEASE BE AWARE:
# THIS MUST BE RUN ONLY ON THE ONLINE LINUX SERVER UNDER DIGITAL OCEAN
#########

import matplotlib
# This is somehow required to import pyplot
matplotlib.use("Agg") 

import os
from ConfigParser import ConfigParser
from time import *
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from glob import glob

# init default values
#dataFolder = "/root/RPi_ADXL_Storage/"
#piIDList = ["RPi-Lui", "RPi-Denny"]
filesAlreadyDrawn = []

def getPlotterSettings(location = "plot_settings.ini"):
	# Use ConfigParser to parse from .ini file for settings
	settings = ConfigParser()
	settings.read(location)
	
	dataFolder = settings.get("PlotSettings", "dataFolder")
	saveLocation = settings.get("PlotSettings", "saveLocation")
	piIDList = settings.get("PlotSettings", "piIDList").split(",")

	return (dataFolder, saveLocation, piIDList)
	
def printPlotterSettings():
	print("[Plotter Settings]")
	print("dataFolder: " + dataFolder)
	print("saveLocation: " + saveLocation)
	print("piIDList:")
	print(piIDList)
	print("\n")

def getLatestFile(dataFolder, piID):
	# Scan folder for latest file and then plot that file
	dataFile = ""
	
	filelist = glob(dataFolder + piID + "/" + piID + "_data*")
	if (len(filelist)==0):
		return -1
	
	# file and datetime
	filesAndDates = {}
	
	
	
	for file in filelist:
		# Parse filename for date
		filename = (file.split("/"))
		
		# Dynamically search for the correct element containing
		# the filename
		for element in filename:
			if "_data_[" in element:
				filename = element
				break
		
		filedate = (filename.split("["))[1]
		filedate = (filedate.split("]"))[0]
		filedate = datetime.strptime(filedate, "%Y-%m-%d_%H-%M-%S")
		# Store in dictionary
		filesAndDates[file] = filedate
	
	latestFile = max(filesAndDates, key=filesAndDates.get)

	return latestFile
	

def parseData(latestDataFile):
	file = open(latestDataFile, "r")
	
	x = []
	y = []
	z = []
	time = []
	data = []

	# Skip first four lines of data file
	for i in range(0,5):
		file.readline()

	for line in file:
		data = line.split(" ")
		x.append(float(data[0]))
		y.append(float(data[1]))
		z.append(float(data[2]))
		
		timeGot = datetime.strptime(data[4].strip(), "%H:%M:%S.%f")
		time.append(timeGot)

	file.close()
	
	return x, y, z, time

def getFilenameFromAddress(filename):
	filename = (filename.split("/"))
	for element in filename:
		if "_data_[" in element:
			return element
			
	return ""
	
	
def plotAxes(x, y, z, time, latestDataFile, piID, saveLocation):
	axesDict = {"x": x, "y": y, "z": z}
	dataTitle = getFilenameFromAddress(latestDataFile)
	
	for axis in axesDict:
		print("Plotting axis " + axis)
		
		plt.figure(figsize=(11,6))
		plt.plot(time, axesDict[axis])
		plt.title(axis + ": " + dataTitle)
		plt.xlabel('Time', fontsize=18)
		plt.ylabel('Acceleration (g)', fontsize=18)
		
		# Extract axes ranges
		x1, x2, y1, y2 = plt.axis()
		
		# Select the larger of the max positive/negative data
		maxPos = min(axesDict[axis]) * -1
		maxNeg = max(axesDict[axis])
		#limitAxis = max([maxPos, maxNeg]) * 1.5
		#plt.axis((x1, x2, limitAxis*-1, limitAxis))
		
		plt.axis((x1, x2, -2.0, 2.0))

		plt.savefig(saveLocation + piID + "/plot_" + axis + ".png")
		plt.clf()
		
	return True

def clearScreen():
	os.system('clear')		
	
######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################	
clearScreen()
(dataFolder, saveLocation, piIDList) = getPlotterSettings()
printPlotterSettings()

interval = float(input("How often are we checking for new files to plot? (in seconds)"))

while True:
	clearScreen()
	# Retrieve latest file in the designated storage folder
	print("Grabbing latest file")
	
	for piID in piIDList:
		latestDataFile = getLatestFile(dataFolder, piID)
		
		if (latestDataFile != -1):
			if (latestDataFile in filesAlreadyDrawn) == False:
				# Parse data for x,y,z,time
				print("Parsing data from " + latestDataFile)
				(x, y, z, time) = parseData(latestDataFile)

				# Plot all three axes and save as png
				print("Plotting all axes")
				plotAxes(x, y, z, time, latestDataFile, piID, saveLocation)
				filesAlreadyDrawn.append(latestDataFile)
			else:
				print(latestDataFile + " has already been drawn!")
		else:
			print("No files found for " + piID)
		
		
	print("\nSleeping for " + str(interval) + " seconds")
	sleep(interval)
