RPi_ADXL
=====================

Work in progress

## 1.0 Installation
Installing the RPi_ADXL source must be done AFTER the Raspberry Pi has been loaded with Raspbian and its appropriate settings configured. Please follow the documentation to properly setup a Raspberry Pi for use with RPi_ADXL

# 1.1 Initial RPi Setup
The Raspberry Pi used and tested in development was the Raspberry Pi 2, specifically the 2B+ model.

The operating system used was the latest Rasbian build available on the raspberrypi.org website. The steps taken to install the OS are also on the website: https://www.raspberrypi.org/help/noobs-setup/. You may also purchase a Raspberry Pi with an SD Card that has NOOBS preinstalled on it.

Once Rasbian has been installed, run "sudo raspi-config" (if it hasn't already come up automatically during setup). Change the clock settings under "4 Internationalisation Options" to Pacific Ocean -> Auckland. This is to ensure that the RPi_ADXL timestamps are accurate. Then, under "8 Advanced Options", turn on SSH & turn on I2C and enable loading by default.

Then run "sudo nano /etc/modules" and add lines as so:
![modulesimage](https://learn.adafruit.com/system/assets/assets/000/003/054/medium800/learn_raspberry_pi_editing_modules_file.png?1396790682)
(courtesy to adafruit.com for image)



