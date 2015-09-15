RPi_ADXL
=====================

Work in progress

# 1.0 Installation
Installing the RPi_ADXL source must be done AFTER the Raspberry Pi has been loaded with Raspbian and its appropriate settings configured. Please follow the documentation to properly setup a Raspberry Pi for use with RPi_ADXL

## 1.1 Initial RPi Setup
The Raspberry Pi used and tested in development was the Raspberry Pi 2, specifically the 2B+ model.

The operating system used was the latest Rasbian build available on the raspberrypi.org website. The steps taken to install the OS are also on the website: https://www.raspberrypi.org/help/noobs-setup/. You may also purchase a Raspberry Pi with an SD Card that has NOOBS preinstalled on it.

Once Rasbian has been installed, run `sudo raspi-config` (if it hasn't already come up automatically during setup). Change the clock settings under "4 Internationalisation Options" to Pacific Ocean -> Auckland. This is to ensure that the RPi_ADXL timestamps are accurate. Then, under "8 Advanced Options", turn on SSH & turn on I2C and enable loading by default.

Then run `sudo nano /etc/modules` and add `i2c-bcm2708 and i2c-dev` lines as so:
![modulesimage](http://i.imgur.com/JLamjTD.png)

This properly configures the i2c modules to run, and should allow our RPi to communicate with the ADXL.

Then run `sudo apt-get upgrade` to ensure your OS is up-to-date.

# 1.2 Security Setup
This is a very important section. The Raspberry Pi's default user and password is "pi" and "raspberry" respectively. If your Raspberry Pi is open to the internet (if you've forwarded its ports through the router), then anyone scanning can hijack your Pi and do whatever they please.

To avoid this, we must immediately take the following steps before opening it to the internet. Otherwise, if you're keeping the RPi_ADXL modules inside a LAN network (or simply uploading data to the internet, but not opening any ports for ssh connection to your RPis) then you can probably skip all the steps under this security section.

1. Change user "pi" password
2. Remove root login (via ssh)
2. Install fail2ban
3. Optional: remove user "pi" password altogether and use ssh keys

### Step 1 - Change user "pi" password



