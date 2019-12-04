
import time
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

while True:
	print(QSerialPortInfo.availablePorts())
	time.sleep(.5)
