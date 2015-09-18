import os
from configparser import ConfigParser

# INCOMPLETE - cannot change any values in config yet!

def checkUserAnswer(input):
	yes = ["yes", "ye", "y", "1", "ok"]
	
	if (input.lower() in yes):
		return True
	else:
		return False

checkUserAnswer(">> Are you sure you wish to install? (this will overwrite any current settings")
#os.system("sudo cp TEMPLATE-RPi_settings.ini RPi_settings.ini")

configFile = ConfigParser()
configFile.read("RPi_settings.ini")
mainSettings = dict(configFile.items("Main"))
uploadSettings = dict(configFile.items("Upload"))

print(mainSettings)
print(uploadSettings)

		