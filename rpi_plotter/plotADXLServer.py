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

from collections import deque

# init default values
#dataFolder = "/root/RPi_ADXL_Storage/"
#piIDList = ["RPi-Lui", "RPi-Denny"]
filesAlreadyRead = []
plotQueue = []

data_plot = dict.fromkeys(["x","y","z","time"])
data_plot["x"] = []
data_plot["y"] = []
data_plot["z"] = []
data_plot["time"] = []

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

def generatePlot(maxCount, plotQueue, data_overflow, dataFolder, piID):
	# This function will generate a list of values to a max length
	dataElementList = ["x", "y", "z", "time"]
	global data_plot
	#data_plot = dict.fromkeys(["x","y","z","time"])
	#data_plot["x"] = []
	#data_plot["y"] = []
	#data_plot["z"] = []
	#data_plot["time"] = []
	
	if ((len(data_plot["x"])) >= maxCount):
		for dataElement in dataElementList:
			data_plot[dataElement] = []
			data_overflow[dataElement] = []
	
	while ((len(data_plot["x"])) < maxCount) and plotQueue:
		dataFilename = plotQueue.popleft()
		data_list = getDataFromFile(dataFilename)
		
		# First check if there's any actual values in data_overflow
		# Split data list into two - take the rest and put into an overflow
		if any(data_overflow.values()):
			for dataElement in dataElementList:
				data_plot[dataElement] += data_overflow[dataElement] + data_list[dataElement][:maxCount]
				data_overflow[dataElement] = data_plot[dataElement][maxCount:]
		else:
			for dataElement in dataElementList:
				data_plot[dataElement] += data_list[dataElement][:maxCount]
				data_overflow[dataElement] = data_plot[dataElement][maxCount:]
		
		filesAlreadyRead.append(dataFilename)
	

	plotAxes(data_plot, "", piID, saveLocation)
	return plotQueue
	
def generatePlotQueue(dataFolder, piID):
	plotQueue = deque()
	
	searchString = dataFolder + piID + "/" + piID + "_data*"
	dataFilenameList = glob(searchString)
	dataFilenameList.sort()

	for dataFilename in dataFilenameList:
		if ((dataFilename in filesAlreadyRead) == False):
			plotQueue.append(dataFilename)
	
	return plotQueue


def getDataFromFile(dataFile):
	fileIsNotFullyUploaded = True
	
	# If we cannot find "end" in the file, we will reread again until we have
	# This is probably process intensive, as we're reading over a file repeatedly
	# Maybe do something with the filename instead?
	while fileIsNotFullyUploaded:
		file = open(dataFile, "r")
		for line in file:
			if "end" in line:
				fileIsNotFullyUploaded = False
		file.close()

	file = open(dataFile, "r")
	x = []
	y = []
	z = []
	time = []
	data_read = []

	# Skip first four lines of data file
	for i in range(0,5):
		file.readline()

	for line in file:
		# Check if we've found the end of the data file
		if ("end" in line) == False:
			data_read = line.split(" ")
			x.append(float(data_read[0]))
			y.append(float(data_read[1]))
			z.append(float(data_read[2]))
			timeRead = datetime.strptime(data_read[4].strip(), "%H:%M:%S.%f")
			time.append(timeRead)
		
	file.close()
	
	data_list = {}
	data_list["x"] = x
	data_list["y"] = y
	data_list["z"] = z
	data_list["time"] = time

	return data_list


def getFilenameFromAddress(filename):
	filename = (filename.split("/"))
	for element in filename:
		if "_data_[" in element:
			return element	
	return ""
	
	
def plotAxes(data_plot, dataFilename, piID, saveLocation):
	axesList = ["x", "y", "z"]
	
	for axis in axesList:
		print("\nPlotting axis " + axis)

		plt.figure(figsize=(11,6))
		plt.plot(data_plot["time"], data_plot[axis])
		plt.title(axis + " - latest: " + dataFilename)
		plt.xlabel('Time', fontsize=18)
		plt.ylabel('Acceleration (g)', fontsize=18)
				
		# Extract axes ranges
		x_range_min, x_range_max, y_range_min, y_range_max = plt.axis()
		
		plt.axis((x_range_min, x_range_max, -2.0, 2.0))

		plt.savefig(saveLocation + piID + "/plot_" + axis + ".png")
		plt.clf()
		plt.close()
		print("Finished plotting!")
		
	return True

def clearScreen():
	os.system('clear')		
	
######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################	
clearScreen()
(dataFolder, saveLocation, piIDList) = getPlotterSettings()
printPlotterSettings()

interval = float(input("How often are we checking for new files to plot? (in seconds)"))

data_overflow = dict.fromkeys(["x","y","z","time"])

while True:
	clearScreen()
	for piID in piIDList:
		plotQueue = generatePlotQueue(dataFolder, piID)
		while plotQueue:
			plotQueue = generatePlot(3000, plotQueue, data_overflow, dataFolder, piID)
		#plotAxes(data_plot, piID, saveLocation)
	print("\nSleeping for " + str(interval) + " seconds")
	sleep(0.5)