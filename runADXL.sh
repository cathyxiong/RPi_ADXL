#!/bin/bash
# Runs both main scripts in separate screens
# Closes screens currently running
# Probably won't interrupt scripts ongoing though

screen -S main -X quit
screen -S upload -X quit

screen -dmS main
screen -dmS upload

screen -S main -X exec clear
screen -S main -X exec sudo python3 /home/pi/mainproject/RPi_ADXL/mainADXL.py -s

screen -S upload -X exec clear
screen -S upload -X exec sudo python3 /home/pi/mainproject/RPi_ADXL/uploadADXL.py -s