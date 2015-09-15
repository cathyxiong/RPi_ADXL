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
3. Install fail2ban
4. Optional: remove user "pi" password altogether and use ssh keys

#### 1.2.1 - Change user "pi" password
In the console, run `passwd`. This will ask you for a new password. Simply input a new password, and it's done. Note that this will only change the password for the user "pi", or whichever user you're currently on.

#### 1.2.2 - Remove root login (vis ssh)
The root user's password is by default also raspberry. However, if we're only worried about remote intrusions, we can leave this as the default password and just disable remote login to the user root. This way if something goes wrong we can always plug our keyboard into our raspberry pi and access root without forgetting some other complicated password.

To remove ssh remote root login, run `sudo nano /etc/ssh/sshd_config`
![permitRootLoginimage](http://i.imgur.com/70DNP2E.png)
Locate the entry `PermitRootLogin` and change the `yes` to `no`, or comment it out. Done.

#### 1.2.3 - Install fail2ban
We can prevent attempts to bruteforce our password (or at least make it harder) by installing fail2ban. fail2ban by default runs as a service and bans any access to the RPi for 10 minutes if an incorrect password has been entered three times. This is configurable. A configuration tutorial is available here: https://www.digitalocean.com/community/tutorials/how-to-protect-ssh-with-fail2ban-on-ubuntu-14-04 under the section "Configure Fail2Ban with your Service Settings". For now we're okay to use the default settings.

Install fail2ban by running `sudo apt-get install fail2ban`. Done.

#### 1.2.4 - Optional: ssh password login altogether and use ssh keys
Note that this step can be dangerous if you do not know what you are doing.

ssh keys work a key pair authentication method. The server has a "public key", and its pair "private key" is what is stored on your local computer. For example, your Raspberry Pi will have a "public key" on it. To connect to your Raspberry Pi from your computer, you must have the "private key" that matches the "public key" on the Pi.

Note that ssh-keys have already been generated for the development and testing of this project, so ask the developer for instructions on where to find the pre-existing public/private keys.

There are multiple ways to generate ssh-key pairs. For this example we'll do it on the Raspberry Pi.

Run `ssh-keygen -t rsa -C "RPi_ADXL"`. Give it a name like "test" and then `ENTER` to continue. You may choose to leave the passphrase as empty (a passphrase adds a password to the private key, adding another authentication step).
![ssh-keygenimage](http://i.imgur.com/mRWDHTo.png)


