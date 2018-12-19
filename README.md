# SSPD
Simple serial port dump

Python utility that helps to capture the log especially from serial ports (including port reconnect feature).

Usage:
```
python sspd.py -h
usage: sspd.py [-h] [-p COM_PORT] [-b BAUDRATE] [-v] [-r]
               [--reconnect-delay SEC]

Simple serial port dump

optional arguments:
  -h, --help            show this help message and exit
  -p COM_PORT, --port COM_PORT
                        serial port; default: ttyUSB0
  -b BAUDRATE, --baudrate BAUDRATE
                        serial port baudrate; default: 115200
  -v                    verbose level: -v, -vv or -vvv (bytes); default: -v
  -r                    reconnect to serial port
  --reconnect-delay SEC
                        reconnect delay, s; default: 2.0
```
