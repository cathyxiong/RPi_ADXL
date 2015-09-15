#!/bin/bash
screen -ls | awk -F. '$NF~"(Detached)" {print "kill -HUP " $1}' | sh

#screen -S main -X quit
#screen -S upload -X quit