#!/bin/bash
# This shell script is a modified script example given in
# https://www.raspberrypi.org/forums/viewtopic.php?t=16054 by MrEngman
# Run this script on CRONTAB to check if connection is down, and if so, reconnect

if ifconfig wlan0 | grep -q "inet addr:" ; then
  sleep 10
else
  echo "Network connection down! Attempting reconnection."
  ifup --force wlan0
  sleep 10
fi