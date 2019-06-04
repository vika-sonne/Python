## Python miscellaneous routines for electronic device developers

## SSPD
Simple serial port dump.

Python utility that helps to capture the log especially from serial ports (USART, e.t.c.) including precise timestamps & bytes and port reconnect features.

Developed as primary logs grabber tool for electronic device developers.

##### Usage:
```sh
$ python sspd.py -h
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
  --bytes               recieve byte by byte
  --reconnect-delay SEC
                        reconnect delay, s; default: 2.0
  --trace-error         show the errors trace; default: off
```
##### Log example:
```sh
$ python sspd.py -r --reconnect-delay 1 -b 250000 -p ttyACM0
2019-06-04T11:59:16.344617 START
11:59:16.344714 Open serial port: /dev/ttyACM0 @ 250000 8N1
12:00:51.544121 09 >> ADC1=843\n
12:00:52.487442 04 >> \tOK\n
12:00:53.805972 10 >> ADC2=3981\n
12:00:54.332748 04 >> \tOK\n
```

## convert_to_h.py
Converts file as binary blob to C/C++ header as array.

##### Usage:
```sh
$ python3 convert_to_h.py -h
usage: convert_to_h.py [-h] -i INPUT_FILEPATH [-o OUTPUT_FILEPATH]
                       [-d ARRAY_DECLARATION]

Converts file as binary blob to C/C++ header as array

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILEPATH
  -o OUTPUT_FILEPATH    if omitted writes to console
  -d ARRAY_DECLARATION  array declaration; default: "unsigned char binary_blob"
```

##### Examples:
```sh
$ python3 convert_to_h.py -i convert_to_h.py
unsigned char binary_blob[1370] = {
0x23, 0x21, 0x2F, 0x75, 0x73, 0x72, 0x2F, 0x62, 0x69, 0x6E, 0x2F, 0x65, 0x6E, 0x76, 0x20, 0x70,
...
0x73, 0x2E, 0x73, 0x74, 0x64, 0x6F, 0x75, 0x74, 0x29, 0xA
};

$ python3 convert_to_h.py -i convert_to_h.py -d "static U8"
static U8[1370] = {
0x23, 0x21, 0x2F, 0x75, 0x73, 0x72, 0x2F, 0x62, 0x69, 0x6E, 0x2F, 0x65, 0x6E, 0x76, 0x20, 0x70,
...
0x73, 0x2E, 0x73, 0x74, 0x64, 0x6F, 0x75, 0x74, 0x29, 0xA
};
```
