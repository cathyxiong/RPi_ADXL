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
import matplotlib.dates as mdates

from datetime import datetime, timedelta
from glob import glob

from collections import deque

import multiprocessing
from multiprocessing import Process, Queue

# init default values
#dataFolder = "/root/RPi_ADXL_Storage/"
#piIDList = ["RPi-Lui", "RPi-Denny"]
filesAlreadyRead = []
plotQueue = []

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

def generateRPiDataStructure(piIDList):
	# Init classes and store into dictionary
	data_RPi_All = {}
	for piID in piIDList:
		data_RPi_All[piID] = dataRPi()

	return data_RPi_All
	
class dataContainer:
	# Contains list of x, y, z, time lists
	def __init__(self):
		# Contains list of x, y, z, time lists
		self.x = []
		self.y = []
		self.z = []
		self.time = []
		
class dataRPi:
	# Contains data for each Pi
	def __init__(self):
		self.data_plot = dataContainer()
		self.data_overflow = dataContainer()

def generatePlotData(dataRPi, maxCount, dataFolder, piID):
	# Generate Plot Data for given piID
	dataElementList = ["x", "y", "z", "time"]
	
	plotQueue = generatePlotQueue(dataFolder, piID)
	
	while plotQueue:	
		data_plot = vars(dataRPi.data_plot)
		data_overflow = vars(dataRPi.data_overflow)
	
		if ((len(data_plot["x"])) >= maxCount):
			for dataElement in dataElementList:
				#data_plot[dataElement] = data_plot[dataElement][1500:] + data_overflow[dataElement]
				data_plot[dataElement] = []
				data_overflow[dataElement] = []
		
		while ((len(data_plot["x"])) < maxCount) and plotQueue:
			dataFilename = plotQueue.popleft()
			data_container = getDataFromFile(dataFilename)
			data_list = vars(data_container)
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
	
		# Might not need this, as data_plot and data_overflow are pointing to the class already
		# So they will update as above. Do it anyway just in case?
		# Set the class variables to the working variables "data_plot", "data_overflow"
		for dataElement in dataElementList:
			setattr(dataRPi.data_plot, dataElement, data_plot[dataElement])
			setattr(dataRPi.data_overflow, dataElement, data_overflow[dataElement])
		
	return dataRPi
		
def plotAllAxes(data_RPi_All, piID, saveLocation):
	# PLOTS FOR ONE PI
	# Using axesList as "time" is in data_plot
	print("Printing all graphs")
	axesList = ["x", "y", "z"]
	
	totalPi = len(data_RPi_All)
	
	plt.figure(1)
	plt.figure(figsize=(10,10))
	
	# For one axis, z
	# Set up subplots
	f_subplot, graph_array = plt.subplots(nrows=totalPi, sharex=True, sharey=True)
	f_subplot.set_figheight(8)
	f_subplot.set_figwidth(16)
	
	position = 0
	for pi in data_RPi_All:
		# Check if pi data_plot actually has data before passing it to be plotted
		if (data_RPi_All[pi].data_plot.x):
			time_axis = data_RPi_All[pi].data_plot.time
			y_axis = data_RPi_All[pi].data_plot.z
			print(pi + " | position: " + str(position))
			graph_array[position].plot(time_axis, y_axis)
			graph_array[position].set_title(str(pi))
			position += 1
	
	
	for ax in graph_array:
		ax.set_ylabel("Accel (g)")
		ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
		ax.yaxis.set_ticks([-2,-1,0,1,2])
		ax.grid(True)
		ax.set_ylabel("Accel (g)")
		
	plt.xlabel('Time', fontsize=18)
	
	x_def_min, x_def_max, y_def_min, y_def_max = plt.axis()

	# Get earliest time out of all Pi Data
	startTimeList = []
	for pi in data_RPi_All:
		if (data_RPi_All[pi].data_plot.time):
			startTimeList.append(data_RPi_All[pi].data_plot.time[0])
	
	# Ensure graph has range of n seconds only from start
	maxSeconds = 80
	startOfGraph = min(startTimeList)
	
	# Round start of time up to the nearest 10 seconds
	# For cleanliness on axis
	etc_num = round(startOfGraph.second, -1)
	startOfGraph -= (timedelta(seconds=(startOfGraph.second - etc_num)))
	endOfGraph = startOfGraph + timedelta(seconds=maxSeconds)
	
	x_ticks = []
	x_ticks.append(startOfGraph)

	tick_interval = 5
	for i in range(maxSeconds/tick_interval):
		x_ticks.append(x_ticks[i] + timedelta(seconds=(tick_interval)))
		
	x_ticks.append(endOfGraph)
	
	plt.axis((startOfGraph, endOfGraph, -2.0, 2.0))
	plt.xticks(x_ticks, rotation='vertical')
	
	plt.savefig(saveLocation + "/plot_z.png")
	
	plt.clf()
	plt.close("all")
		
	print("Printing complete")
	return True

def anyDataExists(data_RPi_All):
	for pi in data_RPi_All:
		if data_RPi_All[pi].data_plot.x:
			return True
	return False

def ignoreExistingData(dataFolder, piIDList):
	# We will add to the "filesAlreadyRead" everything inside the data folder
	# This is to start completely fresh before the plotter begins
	
	for piID in piIDList:
		searchString = dataFolder + piID + "/" + piID + "_data*"
		dataFilenameList = glob(searchString)
	
	for filename in dataFilenameList:
		filesAlreadyRead.append(filename)
		
	
def generatePlotQueue(dataFolder, piID):
	plotQueue = deque()
	
	searchString = dataFolder + piID + "/" + piID + "_data*"
	dataFilenameList = glob(searchString)
	dataFilenameList.sort()

	for dataFilename in dataFilenameList:
		if (dataFilename not in filesAlreadyRead):
			plotQueue.append(dataFilename)
	
	return plotQueue


def getDataFromFile(dataFilename):
	fileIsNotFullyUploaded = True
	
	# If we cannot find "end" in the file, we will reread again until we have
	# This is probably process intensive, as we're reading over a file repeatedly
	# Maybe do something with the filename instead?
	while fileIsNotFullyUploaded:
		dataFile = open(dataFilename, "r")
		for line in dataFile:
			if "end" in line:
				fileIsNotFullyUploaded = False
		dataFile.close()

	dataFile = open(dataFilename, "r")
	x = []
	y = []
	z = []
	time = []
	data_read = []

	# Skip first four lines of data file
	for i in range(0,5):
		dataFile.readline()

	for line in dataFile:
		# Check if we've found the end of the data file
		if ("end" in line) == False:
			data_read = line.split(" ")
			x.append(float(data_read[0]))
			y.append(float(data_read[1]))
			z.append(float(data_read[2]))
			timeRead = datetime.strptime(data_read[4].strip(), "%H:%M:%S.%f")
			time.append(timeRead)
		
	dataFile.close()
	
	data_container = dataContainer()
	data_container.x = x
	data_container.y = y
	data_container.z = z
	data_container.time = time

	return data_container


def getFilenameFromAddress(filename):
	filename = (filename.split("/"))
	for element in filename:
		if "_data_[" in element:
			return element	
	return ""

def clearScreen():
	os.system('clear')		
	
######################################################################################################	 
#### MAIN PROGRAM STARTS HERE ########################################################################	
clearScreen()
(dataFolder, saveLocation, piIDList) = getPlotterSettings()
printPlotterSettings()

#interval = float(input("How often are we checking for new files to plot? (in seconds)"))

# Temporary values before we fix for modular design
maxCount = 6000
ignoringExistingData = True

data_RPi_All = generateRPiDataStructure(piIDList)

if ignoringExistingData:
	ignoreExistingData(dataFolder, piIDList)

while True:
	clearScreen()
	for piID in piIDList:
		data_RPi_All[piID] = generatePlotData(data_RPi_All[piID], maxCount, dataFolder, piID)
	if anyDataExists(data_RPi_All):
		plotAllAxes(data_RPi_All, piID, saveLocation)
	
	print("\nWaiting for new graphs")
	sleep(0.5)