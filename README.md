RPi_ADXL
=====================

Work in progress

# 1.0 Installation
Installing the RPi_ADXL source must be done AFTER the Raspberry Pi has been loaded with Raspbian and its appropriate settings configured. Please follow the documentation to properly setup a Raspberry Pi for use with RPi_ADXL



### 1.1 Raspberry Pi Setup
The Raspberry Pi used and tested in development was the Raspberry Pi 2, specifically the 2B+ model.

The operating system used was the latest Rasbian build available on the raspberrypi.org website. The steps taken to install the OS are also on the website: https://www.raspberrypi.org/help/noobs-setup/. You may also purchase a Raspberry Pi with an SD Card that has NOOBS preinstalled on it.

Once Rasbian has been installed, run `sudo raspi-config` (if it hasn't already come up automatically during setup). Change the clock settings under "4 Internationalisation Options" to Pacific Ocean -> Auckland. This is to ensure that the RPi_ADXL timestamps are accurate. Then, under "8 Advanced Options", turn on SSH & turn on I2C and enable loading by default.

Then run `sudo nano /etc/modules` and add `i2c-bcm2708 and i2c-dev` lines as so:
![modulesimage](http://i.imgur.com/JLamjTD.png)

This properly configures the i2c modules to run, and should allow our RPi to communicate with the ADXL.

Then run `sudo apt-get upgrade` to ensure your OS is up-to-date.



### 1.2 Security Setup
This is a very important section. The Raspberry Pi's default user and password is "pi" and "raspberry" respectively. If your Raspberry Pi is open to the internet (if you've forwarded its ports through the router), then anyone scanning can hijack your Pi and do whatever they please.

To avoid this, we must immediately take the following steps before opening it to the internet. Otherwise, if you're keeping the RPi_ADXL modules inside a LAN network (or simply uploading data to the internet, but not opening any ports for ssh connection to your RPis) then you can probably skip all the steps under this security section.

1. Change user "pi" password
2. Remove root login (via ssh)
3. Install fail2ban
4. Optional: remove user "pi" password altogether and use ssh keys



#### 1.2.1 - Change user "pi" password
In the console, run `passwd`. This will ask you for a new password. Simply input a new password, and it's done. Note that this will only change the password for the user "pi", or whichever user you're currently on. Please try to make this long and secure if you intend on opening the Pi to the internet.



#### 1.2.2 - Remove root login (vis ssh)
The root user's password is by default also raspberry. However, if we're only worried about remote intrusions, we can leave this as the default password and just disable remote login to the user root. This way if something goes wrong we can always plug our keyboard into our raspberry pi and access root without forgetting some other complicated password.

To remove ssh remote root login, run `sudo nano /etc/ssh/sshd_config`
![permitRootLoginimage](http://i.imgur.com/70DNP2E.png)
Locate the entry `PermitRootLogin` and change the `yes` to `no`, or comment it out. Done.



#### 1.2.3 - Install fail2ban
We can prevent attempts to bruteforce our password (or at least make it harder) by installing fail2ban. fail2ban by default runs as a service and bans any access to the RPi for 10 minutes if an incorrect password has been entered three times. This is configurable. A configuration tutorial is available here: https://www.digitalocean.com/community/tutorials/how-to-protect-ssh-with-fail2ban-on-ubuntu-14-04 under the section "Configure Fail2Ban with your Service Settings". For now we're okay to use the default settings.

Install fail2ban by running `sudo apt-get install fail2ban`. Done.



#### 1.2.4 - Optional: ssh password login altogether and only use ssh keys
**DO NOT DO THIS STEP UNTIL AFTER EVERYTHING ELSE IS SET UP**
**You must have a way of copying a private ssh key from your RPi to your PC - but you can't do this without password login in the first place!**

ssh keys work a key pair authentication method. The server has a "public key", and its pair "private key" is what is stored on your local computer. For example, your Raspberry Pi will have a "public key" on it. To connect to your Raspberry Pi from your computer, you must have the "private key" that matches the "public key" on the Pi.

Note that ssh-keys have already been generated for the development and testing of this project, so ask the developer for instructions on where to find the pre-existing public/private keys.

There are multiple ways to generate ssh-key pairs. For this example we'll do it on the Raspberry Pi.

Run `ssh-keygen -t rsa -C "RPi_ADXL"`. Press `ENTER` to continue and save it in its default name/dir. You may choose to leave the passphrase as empty (a passphrase adds a password to the private key, adding another authentication step).
![ssh-keygenimage](http://i.imgur.com/y5sXvWR.png)

Typing `ls /pi/home/.ssh/` should now show two new files: `id_rsa` and `id_rsa.pub`.

Append this to the authorized_key file in the .ssh/ folder by running `/pi/home/.ssh/id_rsa.pub >> /pi/home/.ssh/authorized_keys`. Now your RPi is using this public key to compare with any private keys that attempts to ssh authenticate with it. **It is vital that you have a way of copying this id_rsa file, perhaps through FireZilla.**

**This is why I will not write about how to disable ssh password login, but rather recommend that you change your pi login password to something medium and secure.**



##1.3 Network Setup
If for whatever reason you decide you do not want to use the RPi in a wireless configuration, skip this section as RPis connect to networks via Ethernet by themselves.

Otherwise, continue on below to configure your Pi for wireless access.



####1.3.1 Configuring WiFi
As the Raspberry Pi website already have great documentation on how to setup WiFi, please refer to the below links to set your Pi up with wireless. You MUST have a wireless adapter, such as USB WiPi for wireless to work.

Configuring via GUI: https://www.raspberrypi.org/documentation/configuration/wireless/
Configuring via Command Line: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md



####1.3.2 Hostname
You may give your RPi an alias, such as RPi-Lui, for ease of identification in the network.

Type `sudo raspi-config`. Under "8 Advanced Options" > "A2 Hostname", you may input the hostname of your Pi.

This completes the Raspberry Pi setup. Any step after this can be completed via SSH remote login, or can be carried on while still on the RPi locally.



#2.0 Installing RPi_ADXL Dependencies
RPi_ADXL uses THREE other modules in order to work (that is not included in the source), which is used for its ability to upload files via SCP to a remote server by Python3.

- plumbum
- git
- screen

#####A: One of the modules is called `plumbum` and is only available via another package-installer `pip`. Therefore you must install it in these steps (to also ensure that you are downloading the Python3 version of plumbum):

1. Install pip3.2 by running `sudo apt-get install python3-pip`
2. Install plumbum by running `sudo pip-3.2 install plumbum`


#####B: The second module is `git` which we use to push/pull updates to our master repository online on GitHub. Install like so:

1. Run `sudo apt-get install git`


#####C: The third module is 'screen' which is used to keep sessions persistent even after logging out of our ssh session

1. Run `sudo apt-get install screen`





###2.1 Installing the RPi_ADXL source
The RPi_ADXL program can be installed anywhere, as its target folders can work independently of where it's located.

To be safe, we'll put it in the same directory used during dev/test. This is in `/home/pi/mainproject/`.

Therefore run `cd /home/pi/` and then run `mkdir mainproject` to create a mainproject folder. Then switch to that folder by typing `cd mainproject`.

Once inside the directory `/home/pi/mainproject/` we will then use git to clone the source from GitHub. An alternative is if you have a .zip containing the source, you may unzip it in here and in its own folder named "RPi_ADXL".

To clone RPi_ADXL, simply run `git clone https://github.com/theSpeare/RPi_ADXL.git`. This will then grab the source online and put it into a folder named RPi_ADXL inside `/home/pi/mainproject/`. Congratulations - RPi_ADXL is now installed. Only one more thing to do to complete our setup.




###2.2 Setup our RPi_settings.ini file
As of the time this readme was written, the RPi_settings.ini file is stored on the repo as "TEMPLATE-RPi_settings.ini". To enable our settings, copy and paste this file as "RPi_settings.ini". **It is important you do not simply delete or rename the TEMPLATE file, due to git tracking issues.**

To copy and paste the file as RPi_settings.ini: make sure you are in the folder containing the source, for example: `/home/pi/mainproject/RPi_ADXL/` then run `cp TEMPLATE-RPi_settings.ini RPi_settings.ini`. Verify the results by typing `-ls` and checking that there is now a separate RPi_settings.ini file.

**VERY IMPORTANT** The RPi_ADXL identifies itself uniquely against others with an ID inside the RPi_settings.ini file. Make sure you change the ID to something unique that no other RPi_ADXL is using.

To edit the .ini file, run `sudo nano RPi_settings.ini`. Change the entry under `piID=RPi-Lui` to `piID=RPi-<insertwhatevernameyouwanthere>`.

![piIDimage](http://i.imgur.com/caDGMXv.png)

Congratulations! You have completed setting up your Raspberry Pi for RPi_ADXL use.



#3.0 Configuring the RPi_ADXL
###3.1 RPi_settings.ini

###3.2 Remote Server Configuration

#4.0 Running the RPi_ADXL
###4.1 Running the Main RPi_ADXL Scripts
###4.2 Running the Scripts with Screen
###4.3 Killing the Scripts
