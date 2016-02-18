RPi_ADXL
=====================

# Table of Contents
0.0 [General Information](https://github.com/theSpeare/RPi_ADXL#00-general-information)<br><br><br>
1.0 [Installation](https://github.com/theSpeare/RPi_ADXL#10-installation)<br>
__1.1 [Raspberry Pi Setup](https://github.com/theSpeare/RPi_ADXL#11-raspberry-pi-setup)<br>
__1.2 [Security Setup](https://github.com/theSpeare/RPi_ADXL#12-security-setup)<br>
__1.3 [Network Setup](https://github.com/theSpeare/RPi_ADXL#13-network-setup)<br>
<br><br>
2.0 [Installing RPi_ADXL Dependencies](https://github.com/theSpeare/RPi_ADXL#20-installing-rpi_adxl-dependencies)<br>
__2.1 [Installing the RPi_ADXL Source](https://github.com/theSpeare/RPi_ADXL#21-installing-the-rpi_adxl-source)<br>
__2.2 [Setup RPi_settings.ini file](https://github.com/theSpeare/RPi_ADXL#22-setup-our-rpi_settingsini-file)<br>
<br><br>
3.0 [Configuring the RPi_ADXL](https://github.com/theSpeare/RPi_ADXL#30-configuring-the-rpi_adxl)<br>
__3.1 [RPi_settings.ini](https://github.com/theSpeare/RPi_ADXL#31-rpi_settingsini)<br>
__3.2 [Private ssh key for connecting and uploading to remote server](https://github.com/theSpeare/RPi_ADXL#32-private-ssh-key-for-connecting-and-uploading-to-remote-server)<br>
__3.3 [Remote Server Configuration](https://github.com/theSpeare/RPi_ADXL#33-remote-server-configuration)<br>
<br><br>
4.0 [Running RPi_ADXL](https://github.com/theSpeare/RPi_ADXL#40-running-the-rpi_adxl)<br>
__4.1 [Running the Main RPi_ADXL Scripts](https://github.com/theSpeare/RPi_ADXL#41-running-the-main-rpi_adxl-scripts)<br>
__4.2 [Running the Scripts with Screen](https://github.com/theSpeare/RPi_ADXL#42-running-the-scripts-with-screen)<br>

<br><br>
# 0.0 General Information
All scripts written by Lui Villarias. All modules and libraries referenced were written by their respective authors under GPL license.

Libraries used were: 
- plumbum @ https://pypi.python.org/pypi/plumbum
- i2clibraries by ThinkBowl @ https://github.com/quick2wire/quick2wire-python-api
- all other libraries used are general Python modules

Main scripts used:
- mainADXL.py - runs all main functions
- rpi_plotter/plotADXLServer.py - run on the remote server to plot to website
- checkForConnections.sh - run on CRONTAB to reconnect WiFi when downed
<br>

# 1.0 Installation
Installing the RPi_ADXL source must be done AFTER the Raspberry Pi has been loaded with Raspbian and its appropriate settings configured. Please follow the documentation to properly setup a Raspberry Pi for use with RPi_ADXL
<br><br><br>

### 1.1 Raspberry Pi Setup
The Raspberry Pi used and tested in development was the Raspberry Pi 2, specifically the 2B+ model.

The operating system used was the latest Rasbian build available on the raspberrypi.org website. The steps taken to install the OS are also on the website: https://www.raspberrypi.org/help/noobs-setup/. You may also purchase a Raspberry Pi with an SD Card that has NOOBS preinstalled on it.

Once Rasbian has been installed, run `sudo raspi-config` (if it hasn't already come up automatically during setup). Change the clock settings under "4 Internationalisation Options" to Pacific Ocean -> Auckland. This is to ensure that the RPi_ADXL timestamps are accurate. Then, under "8 Advanced Options", turn on SSH & turn on I2C and enable loading by default.

Then run `sudo nano /etc/modules` and add `i2c-bcm2708 and i2c-dev` lines as so:
![modulesimage](http://i.imgur.com/JLamjTD.png)

This properly configures the i2c modules to run, and should allow our RPi to communicate with the ADXL.

Then run `sudo apt-get upgrade` to ensure your OS is up-to-date.
<br><br><br>

#### 1.1.1 Connecting the ADXL 345
Power off the Raspberry Pi. 
If you are using the Adafruit ADXL 345: Connect GND to GND, 3V to 3V3, SDA to SDA and SCL to SCL.
If you are using the Sparkfun ADXL 345: Connect GND to ground, VCC to 3.3V, CS to 3.3V, SDO to ground, SDA to SDA and SCL to SCL. 

If using the Sparkfun ADXL 345 next power up the Raspberry Pi and type `sudo apt-get install python-smbus i2c-tools git-core`. Test the ADXL345 is found on the I2C bus by running `sudo i2cdetect -y 1` and you should see a device at address 53. After installing the RPi_ADXL source file change directory to RPi_ADXL and run `sudo python3 barPrintTest.py` to check the accelerometer works.
<br><br><br>

### 1.2 Security Setup
This is a very important section. The Raspberry Pi's default user and password is "pi" and "raspberry" respectively. If your Raspberry Pi is open to the internet (if you've forwarded its ports through the router), then anyone scanning can hijack your Pi and do whatever they please.

To avoid this, we must immediately take the following steps before opening it to the internet. Otherwise, if you're keeping the RPi_ADXL modules inside a LAN network (or simply uploading data to the internet, but not opening any ports for ssh connection to your RPis) then you can probably skip all the steps under this security section.

1. Change user "pi" password
2. Remove root login (via ssh)
3. Install fail2ban
4. Optional: remove user "pi" password altogether and use ssh keys
<br><br><br>


#### 1.2.1 - Change user "pi" password
In the console, run `passwd`. This will ask you for a new password. Simply input a new password, and it's done. Note that this will only change the password for the user "pi", or whichever user you're currently on. Please try to make this long and secure if you intend on opening the Pi to the internet.
<br><br><br>


#### 1.2.2 - Remove root login (vis ssh)
The root user's password is by default also raspberry. However, if we're only worried about remote intrusions, we can leave this as the default password and just disable remote login to the user root. This way if something goes wrong we can always plug our keyboard into our raspberry pi and access root without forgetting some other complicated password.

To remove ssh remote root login, run `sudo nano /etc/ssh/sshd_config`
![permitRootLoginimage](http://i.imgur.com/70DNP2E.png)<br>
Locate the entry `PermitRootLogin` and change the `yes` to `no`, or comment it out. Done.
<br><br><br>


#### 1.2.3 - Install fail2ban
We can prevent attempts to bruteforce our password (or at least make it harder) by installing fail2ban. fail2ban by default runs as a service and bans any access to the RPi for 10 minutes if an incorrect password has been entered three times. This is configurable. A configuration tutorial is available here: https://www.digitalocean.com/community/tutorials/how-to-protect-ssh-with-fail2ban-on-ubuntu-14-04 under the section "Configure Fail2Ban with your Service Settings". For now we're okay to use the default settings.

Install fail2ban by running `sudo apt-get install fail2ban`. Done.
<br><br><br>


#### 1.2.4 - Optional: ssh password login altogether and only use ssh keys
**DO NOT DO THIS STEP UNTIL AFTER EVERYTHING ELSE IS SET UP**
**You must have a way of copying a private ssh key from your RPi to your PC - but you can't do this without password login in the first place!**

ssh keys work a key pair authentication method. The server has a "public key", and its pair "private key" is what is stored on your local computer. For example, your Raspberry Pi will have a "public key" on it. To connect to your Raspberry Pi from your computer, you must have the "private key" that matches the "public key" on the Pi.

Note that ssh-keys have already been generated for the development and testing of this project, so ask the developer for instructions on where to find the pre-existing public/private keys.

There are multiple ways to generate ssh-key pairs. For this example we'll do it on the Raspberry Pi.

Run `ssh-keygen -t rsa -C "RPi_ADXL"`. Press `ENTER` to continue and save it in its default name/dir. You may choose to leave the passphrase as empty (a passphrase adds a password to the private key, adding another authentication step).<br>
![ssh-keygenimage](http://i.imgur.com/y5sXvWR.png)<br>

Typing `ls /home/pi/.ssh/` should now show two new files: `id_rsa` and `id_rsa.pub`.

Append this to the authorized_key file in the .ssh/ folder by running `/home/pi/.ssh/id_rsa.pub >> /home/pi/.ssh/authorized_keys`. Now your RPi is using this public key to compare with any private keys that attempts to ssh authenticate with it. **It is vital that you have a way of copying this id_rsa file, perhaps through FireZilla.**

**This is why I will not write about how to disable ssh password login, but rather recommend that you change your pi login password to something medium and secure.**
<br><br><br>


##1.3 Network Setup
If for whatever reason you decide you do not want to use the RPi in a wireless configuration, skip this section as RPis connect to networks via Ethernet by themselves.

Otherwise, continue on below to configure your Pi for wireless access.
<br><br><br>


####1.3.1 Configuring WiFi
As the Raspberry Pi website already have great documentation on how to setup WiFi, please refer to the below links to set your Pi up with wireless. You MUST have a wireless adapter, such as USB WiPi for wireless to work.

Configuring via GUI: https://www.raspberrypi.org/documentation/configuration/wireless/
Configuring via Command Line: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md
<br><br><br>


####1.3.2 Setting up static IP
Setting up a static IP means you can ssh into the raspberry pi using the same ip address. 
Follow these instructions for setting up a static IP: http://www.circuitbasics.com/how-to-set-up-a-static-ip-on-the-raspberry-pi/ 
Except do not add these lines `interface eth0 static ip_address=10.0.0.100` as a static ethernet ip address is not required.
<br><br><br>

####1.3.3 Hostname
You may give your RPi an alias, such as RPi-Lui, for ease of identification in the network.

Type `sudo raspi-config`. Under "8 Advanced Options" > "A2 Hostname", you may input the hostname of your Pi.

This completes the Raspberry Pi setup. Any step after this can be completed via SSH remote login, or can be carried on while still on the RPi locally.
<br><br><br>


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



<br><br><br>

###2.1 Installing the RPi_ADXL source
The RPi_ADXL program can be installed anywhere, as its target folders can work independently of where it's located.

To be safe, we'll put it in the same directory used during dev/test. This is in `/home/pi/mainproject/`.

Therefore run `cd /home/pi/` and then run `mkdir mainproject` to create a mainproject folder. Then switch to that folder by typing `cd mainproject`.

Once inside the directory `/home/pi/mainproject/` we will then use git to clone the source from GitHub. An alternative is if you have a .zip containing the source, you may unzip it in here and in its own folder named "RPi_ADXL".

To clone RPi_ADXL, simply run `git clone https://github.com/theSpeare/RPi_ADXL.git`. This will then grab the source online and put it into a folder named RPi_ADXL inside `/home/pi/mainproject/`. Congratulations - RPi_ADXL is now installed. Only one more thing to do to complete our setup.



<br><br><br>
###2.2 Setup our RPi_settings.ini file
As of the time this readme was written, the RPi_settings.ini file is stored on the repo as "TEMPLATE-RPi_settings.ini". To enable our settings, copy and paste this file as "RPi_settings.ini". **It is important you do not simply delete or rename the TEMPLATE file, due to git tracking issues.**

To copy and paste the file as RPi_settings.ini: make sure you are in the folder containing the source, for example: `/home/pi/mainproject/RPi_ADXL/` then run `cp TEMPLATE-RPi_settings.ini RPi_settings.ini`. Verify the results by typing `-ls` and checking that there is now a separate RPi_settings.ini file.

**VERY IMPORTANT** The RPi_ADXL identifies itself uniquely against others with an ID inside the RPi_settings.ini file. Make sure you change the ID to something unique that no other RPi_ADXL is using.

To edit the .ini file, run `sudo nano RPi_settings.ini`. Change the entry under `piID=RPi-Lui` to `piID=RPi-<insertwhatevernameyouwanthere>`.

![piIDimage](http://i.imgur.com/caDGMXv.png)

Congratulations! You have completed setting up your Raspberry Pi for RPi_ADXL use.


<br><br><br>
#3.0 Configuring the RPi_ADXL
###3.1 RPi_settings.ini

RPi_settings.ini contains all of the configurable settings that runs with mainADXL.py. See below for example:

RPi_settings.ini:
````
[RPi]
piID=RPi-Lui

[Main]
# save_interval is in minutes
adxl_interval = 0.01
save_interval = 1
checkForSignificance = True
x_thresh = 0.4
y_thresh = 0.4
z_thresh = 0.4
up_orient = z
east_orient = x
north_orient = y

[Upload]
# uploadInterval is in minutes
uploading=True
uploadUser=upload
uploadHost=104.236.141.183
uploadDirectory=/home/upload/RPi_ADXL_Storage/
uploadInterval = 1
dataFolder=ADXLData/
````

- **piID** - The unique ID manually given to the RPi
- **adxl_interval** - The ADXL getAxes() frequency in seconds. For example, a value of 0.01 will attempt to grab axes values per 0.01 seconds.
- **save_interval** - How long mainADXL.py will collect data for before writing a file in the local data folder.
- **checkForSignificance** - If True, mainADXL.py will ONLY write files that have gone over the given threshold values.
- **_thresh** - In g's, these values are the thresholds `checkForSignificance` will look for to see if anything significant has been recorded. Anything below these thresholds will be ignored if checkForSignificance = True.
- **_orient** - Input here what orientation the ADXLs are placed - this is for reference only, and will be printed to the file.
- **uploadng** - Boolean True/False to enable/disable uploading
- **uploadUser** - The user used to upload files in the remote server
- **uploadHost** - Remote server IP
- **uploadDirectory** - The remote directory for upload.
- **uploadInterval** - How often uploadADXL will loop to check for any new files to upload.
- **dataFolder** - The local data folder (default "ADXLData/") used to store data & log files.

<br><br><br>
###3.2 Private ssh key for connecting and uploading to remote server
mainADXL.py uploads to remote server by ssh key authentication. On dev/testing we use the user `upload@104.236.141.183` on a virtual linux server hosted in San Fransisco. The ssh keys have already been generated during dev/testing, so please ask the developer for the private key if you are adding new RPi_ADXLs (or simply want to ssh into the server).

**The SSH private key must be placed in /home/pi/.ssh/** as the key location & name were made non-configurable outside of the script intentionally. After placing the private key in the folder try to ssh into the remote server from the pi. `ssh upload@104.236.141.183`. If you get a message permissions are too open private key is ignored type `chmod 600 /home/pi/.ssh/id_rsa` so only the owner can read and write to the private key. If you type `ssh upload@104.236.141.183` again you should be able to ssh into the remote server without requiring a password.


**Without the proper SSH private key, your upload will fail to authenticate and the server will refuse you connection, effectively failing upload**

<br><br><br>
###3.3 Remote Server Configuration
For dev/testing, the user "upload" was created on the remote server for uploading data/log files. The configuration on the remote server is incredibly easy. First, ensure the server running has the correct public ssh key that's paired with the RPi_ADXLs that are uploading. The same steps can be used above, or you can look up plenty of tutorials on how to set this up.

Next, each RPi_ADXL requires a folder of its own on the remote server. This is where it will upload its files to. Make sure when you create these folders that you are creating these folders under the user "upload", and not "root", otherwise you will have user permission issues.

The default remote server location for data file storage is /home/upload/RPi_ADXL_Storage/
This directory is of course configurable in the RPi_settings.ini. Therefore if you wish to put your RPi_ADXL_Storage folder elsewhere in your server, simply make sure that the `uploadDirectory` setting in the RPi_settings.ini is changed to reflect this. Again, you must be careful to have all folders created by the user `upload` to avoid permission issues.

There should be one folder per RPi_ADXL in the RPi_ADXL_Storage directory. For example, with four RPi's: RPi-Denny, RPi-Lui, RPi-Quincy, RPi-Wing, there will be four folders.

/home/upload/RPi_ADXL_Storage/RPi-Lui/
/home/upload/RPi_ADXL_Storage/RPi-Denny/
/home/upload/RPi_ADXL_Storage/RPi-Quincy/
/home/upload/RPi_ADXL_Storage/RPi-Wing/

Every time you add new RPis to the system you must add new folders here to give them somewhere to upload to.

**Note that `uploadDirectory` in RPi_settings.ini should only point to `/home/upload/RPi_ADXL_Storage/` as mainADXL.py will find the correct unique folder by itself with its piID**

<br><br><br>
#4.0 Running the RPi_ADXL
RPi_ADXL is run by two main scripts: `mainADXL.py`. These are run with `python3`. Other scripts included in the script are used for testing/debugging purposes.

**Note in LINUX: Press CTRL+C to interrupt a script and terminate it.**

<br><br><br>
###4.1 Running the Main RPi_ADXL Scripts
####mainADXL.py
Run mainADXL.py with `sudo python3 mainADXL.py`
`sudo` is required for this as linux requires `sudo` permissions to interface with the i2c bus in order to communicate with the ADXL.

The script will then display some options. These are self-explanatory and you can refer to the [settings.ini section](https://github.com/theSpeare/RPi_ADXL#31-rpi_settingsini). All these default input settings can be configured via RPi_settings.ini and will load upon restarting the script.

####Skipping Input Stage
Both scripts can be run with an argument from the console to skip the input stage in either script and just use default config values. To do this, you simply add "-s" or "--skipinput" at the end of your python call command.

`sudo python3 mainADXL.py -s`

This will allow you to quickly start the scripts without having to input anything. This will also be even more useful when we use Screen.

####uploadADXL.py
As of the latest version, uploadADXL.py has been merged to mainADXL.py as a parallel process.

<br><br><br>
###4.2 Running the Scripts with Screen
A screen session can be started with the command `screen`. Likewise, a screen session can be created and named with the command `screen -Y <name>`. To list screen sessions use the command `screen -ls`, you can then reconnect to a desired listed session with `screen -r <the_screen>`.

Every screen is essentially a pesistent session, allowing the user to attach and detach at any time while being able to log out. Once in a session, you must always detach with `CTRL+D` before exiting.

Execute all main scripts within a screen to keep them persistent and running even after you've logged off.

<br><br><br>
###4.3 Killing the Scripts
Killing mainADXL.py can be done by pressing `CTRL+C` in the console. However due to generic try/catches, you must hold `CTRL+C` for awhile until every multiprocess in the script has been killed.

Another alternative is to use `killall python3` or `killall python` to kill all running python processes. This is the most reliable, but most abrupt way to do so.
