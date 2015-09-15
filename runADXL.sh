#!/bin/bash

sh stopADXL.sh

screen -dmS main
screen -dmS upload

screen -S main -X exec clear
screen -S main -X exec sudo python3 /home/pi/mainproject/RPi_ADXL/mainADXL.py -s

screen -S upload -X exec clear
screen -S upload -X exec sudo python3 /home/pi/mainproject/RPi_ADXL/uploadADXL.py -s