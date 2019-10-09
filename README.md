## Python miscellaneous routines for electronic device developers

This python 3 routines is ready to use for Linux & Windows. Although the Linux is primary OS for me and this routines well tested for it.

Installation required modules by [pip](https://pip.pypa.io/en/stable/installing/):
```sh
pip install argparse, pyserial
```


## SSPD
Simple serial port dump.

Python utility that helps capturing the log especially from serial ports (USART, e.t.c.) and includes features:
* precise timestamps (μs for Linux, ms for Windows);
* C-style escape for bytes dump;
* port reconnect;
* USB port search by VID:PID.

Developed as primary logs grabber tool for electronic device developers.

##### Usage:
```sh
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
  --bytes               receive byte by byte
  --reconnect-delay SEC
                        reconnect delay, s; default: 2.0
  --vid-pid VID:PID     search for USB: VendorID:ProductID[,VendorID:ProductID[...]]; example: 03eb:2404,03eb:6124
  --trace-error         show the errors trace; default: off
```

##### Usage examples:
* Reconnect & USB VID:PID search (Atmel μC):
```sh
python sspd.py -r --vid-pid 03eb:2404,03eb:6124
```

* Reconnect (with period 1s), baudrate & port (for Linux):
```sh
sspd.py --reconnect-delay 1 -rb 250000 -p ttyACM0
```

* Unbuffered python stdout, reconnect, port & write to log file and console simultaneously (for Linux):
```sh
python -u sspd.py -rp ttyACM0 | tee ~/1.log
```

* Unbuffered python stdout, reconnect, port, log file name is current date_time (example: 2019-09-10_19-37-59.log) (for Linux):
```sh
python -u sspd.py -rp ttyACM0 > ~/$(date +"%Y-%d-%m_%H-%M-%S").log
```

##### Log example:
```sh
python sspd.py -r --reconnect-delay 1 -b 250000 -p ttyACM0
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
python3 convert_to_h.py -h
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
python3 convert_to_h.py -i convert_to_h.py
unsigned char binary_blob[1370] = {
0x23, 0x21, 0x2F, 0x75, 0x73, 0x72, 0x2F, 0x62, 0x69, 0x6E, 0x2F, 0x65, 0x6E, 0x76, 0x20, 0x70,
...
0x73, 0x2E, 0x73, 0x74, 0x64, 0x6F, 0x75, 0x74, 0x29, 0xA
};

python3 convert_to_h.py -i convert_to_h.py -d "static U8"
static U8[1370] = {
0x23, 0x21, 0x2F, 0x75, 0x73, 0x72, 0x2F, 0x62, 0x69, 0x6E, 0x2F, 0x65, 0x6E, 0x76, 0x20, 0x70,
...
0x73, 0x2E, 0x73, 0x74, 0x64, 0x6F, 0x75, 0x74, 0x29, 0xA
};
```

## ASPC
Atmel Studio Project file Converter. Python 2 command-line utility that helps migrate projects to Eclipse.
Usually C/C++ project has many include paths & defines, so the main problem is correct copy this items to Eclipse. Mainly, project files represent by one xml file. So it is enough to copy xml data between import & export files. This utility helps done this in semi-automatic way.

After running this utility several files will be created:
- *eclipse cproject.xml* file contains *sourceEntries/entry* xml tags with list of project files. This piece of xml data need to insert into Eclipse *.cproject* file. Or skip this copying and configure excluded files manually in Eclipse project tree.
- *eclipse settings '(Configuration)' == 'CONFIGURATION_NAME'.xml* files (one per configuration) contains include paths & defines to import on the Eclipse  project property page *"C/C++ General" / "Paths and Symbols"* by button *"Import Settings..."*.
- Also output can be redirected to *.htm* file to view project properties, configurations e.t.c.

## Generate UUID
Prints out the UUID as C/C++ array as hex values.

Example:
```
python generate_uuid.py 
{ 0xB3, 0xE9, 0x63, 0x2C, 0xC0, 0xB4, 0x43, 0xAB, 0x99, 0x60, 0x8A, 0x7E, 0x93, 0x55, 0x29, 0x5A };
```