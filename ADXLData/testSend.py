import ftplib

session = ftplib.FTP()
session.connect('192.168.0.100', 45557)
session.login('lui', 'quincy')

file = open('ADXLdata_01','rb')
session.storbinary('STOR ADXLdata_01', file)
file.close()
session.quit()