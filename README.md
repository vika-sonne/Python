## Python miscellaneous routines for electronic device developers

This python 3 routines is ready to use for Linux & Windows. Although the Linux is primary OS for me and this routines well tested for it.

Installation required modules by [pip](https://pip.pypa.io/en/stable/installing/):
```sh
pip install argparse, pyserial
```


## SSPD
**Simple serial port dump.**

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
**Atmel Studio project file Converter.**

Command-line utility that helps migrate Atmel Studio projects to Eclipse CDT (GNU MCU Eclipse plug-in) projects.

Usually C/C++ project has many include paths & defines (symbols), so the main problem is correct copy this items to Eclipse. Mainly, project represent by one xml file: *.cproj* for Atmel Studio and *.cproject* for Eclipse CDT. So it is enough to copy xml data between project files. This utility helps done this in semi-automatic way.

### Usage

```sh
python3 aspc.py -h
usage: aspc.py [-h] [-v] -p PROJECT_FILE {info,htm,eclipse,sh} ...

Atmel Studio project conversion

positional arguments:
  {info,htm,eclipse,sh}
    info                print the Atmel Studio project information
    htm                 print the html report
    eclipse             export to Eclipse CDT project
    sh                  export to build shell script

optional arguments:
  -h, --help            show this help message and exit
  -v                    verbose level: -v; default: no verbose
  -p PROJECT_FILE, --project-file PROJECT_FILE
                        Atmel Studio project file path

Copyright (C) Victoria Danchenko, 2019.
```

#### Example of *info* command:
```sh
python3 aspc.py info -h
usage: aspc.py info [-h] [-c CONDITION] {conditions,include,exclude,defines}

positional arguments:
  {conditions,include,exclude,defines}

optional arguments:
  -h, --help            show this help message and exit
  -c CONDITION, --condition CONDITION
                        name of Atmel Studio project build condition; optional
```

This command can be used to get names of build conditions:
```sh
python aspc.py -p atmel_studio_project.cproj info conditions
```

#### Example of *html* command:
```sh
python3 aspc.py htm -h
usage: aspc.py htm [-h]

optional arguments:
  -h, --help  show this help message and exit
```

This command useful to get detailed information about Atmel Studio project:
```sh
python aspc.py -p atmel_studio_project.cproj html > report.htm
```

#### Example of *eclipse* command (it can help to export Atmel Studio project to Eclipse CDT project):
```sh
python3 aspc.py eclipse -h
usage: aspc.py eclipse [-h] {include-and-symbols,excluding} ...

positional arguments:
  {include-and-symbols,excluding}
                        export to Eclipse CDT project
    include-and-symbols
                        print Eclipse settings xml file to import to CDT
                        project on "C/C++ General/Path and Symbols" tab of
                        project properties. Contains xml tag
                        <cdtprojectproperties>
    excluding           print Eclipse CDT project excluding files. Contains
                        part of CDT project file: two xml tags
                        <sourceEntries><entry excluding="..."></sourceEntries>

optional arguments:
  -h, --help            show this help message and exit
```

##### Export includes & defines to *settings.xml* file:
```sh
python aspc.py -p atmel_studio_project.cproj eclipse include-and-symbols -h
usage: aspc.py eclipse include-and-symbols [-h] -c CONDITION
                                           [--include-path-remove-prefix INCLUDE_PATH_REMOVE_PREFIX]

optional arguments:
  -h, --help            show this help message and exit
  -c CONDITION, --condition CONDITION
                        name of Atmel Studio project build condition
  --include-path-remove-prefix INCLUDE_PATH_REMOVE_PREFIX
```

###### Example to get Eclipse CDT *settings.xml* file:
```sh
python aspc.py -p atmel_studio_project.cproj eclipse include-and-symbols -c "'\$(Configuration)' == 'CONDITION_NAME'" > settings.xml
```
To get *CONDITION_NAME* use *info* command.

Import *settings.xml* file by pressing button *Import Settings...* on "C/C++ General/Path and Symbols" tab of project properties.

##### Export excluded files to *.cproject* file:
```sh
python aspc.py -p atmel_studio_project.cproj eclipse excluding > exclude.xml
```
Copy contents of *exclude.xml* file to <sourceEntries> xml tag of *.cproject* file.

#### Example of *sh* command (it can help to build Atmel Studio project by Linux command shell):
```sh
python3 aspc.py sh -h
usage: aspc.py sh [-h] [--src-path PATH] -c CONDITION [--cc CC] [--ld LD]
                  [--cflags CFLAGS] [--ldflags LDFLAGS]
                  [--toolchain-path PATH] [--target-file TARGET_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --src-path PATH       path to sources to compile; default: ../
  -c CONDITION, --condition CONDITION
                        name of Atmel Studio project build condition
  --cc CC               toolchain C compiler; default: gcc
  --ld LD               toolchain linker; default: gcc
  --cflags CFLAGS       C compiler flags; optional
  --ldflags LDFLAGS     linker flags; optional
  --toolchain-path PATH
                        path to toolchain excecutables; optional; example:
                        /opt/gcc-arm-none-eabi-9-2019-q4-major/bin
  --target-file TARGET_FILE
                        Target file; default: a.out; example: target.elf
```

Example to get Linux command shell file for ARM Cortex-M4:
```sh
python aspc.py -p atmel_studio_project.cproj sh --cc arm-none-eabi-gcc --ld arm-none-eabi-gcc --toolchain-path /opt/gcc-arm-none-eabi-9-2019-q4-major/bin/ -c "'\$(Configuration)' == 'CONDITION_NAME'" --cflags " -DSOME_DEFINE -mcpu=cortex-m4 -mthumb -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -g3 -c" --target-file project.elf > build_broject.sh
```
To get *CONDITION_NAME* use *info* command.

## Generate UUID
Prints out the UUID as C/C++ array as hex values.

Example:
```
python generate_uuid.py 
{ 0xB3, 0xE9, 0x63, 0x2C, 0xC0, 0xB4, 0x43, 0xAB, 0x99, 0x60, 0x8A, 0x7E, 0x93, 0x55, 0x29, 0x5A };
```
