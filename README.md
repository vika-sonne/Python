## :snake: Python miscellaneous routines for electronic device developers :robot:

This python 3 routines is ready to use for Linux & Windows. Although the Linux is primary OS for me and this routines well tested for it.

Installation required modules by [pip](https://pip.pypa.io/en/stable/installing/):
```sh
pip install argparse, pyserial, Pillow
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

## ESP32 DFU protocol parser
Dumps request/response commands in SLIP packets.

Example of ESP32 programming dump with [sspd Qt version](https://github.com/vika-sonne/sspd-qt):
```sh
parallel -j2 -- './sspd -tu 10c4:ea60 -b 115200 | python3 sspd_esp32_parser.py' './sspd -tu 10c4:ea60 -b 115200 | python3 sspd_esp32_parser.py'
Skip 1 bytes: \x00
Skip 1 bytes: \x00
Skip 1 bytes: \x00
Skip 1 bytes: \x00
Skip 1 bytes: \x00
Skip 1 bytes: \x00
12:41:19.259 request SYNC
12:41:19.411 request SYNC
12:41:19.561 request SYNC
12:41:19.712 request SYNC
Skip 201 bytes: Started Serial0 and LEDanimation\r\n1\r\nStarted Serial0 and LED animation\r\nets Jun  8 2016 00:22:57\r\n\r\nrst:0x1 (POWERON_RESET),boot:0x1 (DOWNLOAD_BOOT(UART0/UART1/SDIO_FEI_REO_V2))\r\nwaiting for download\r\n
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.722 response SYNC
12:41:19.723 request READ_REG {'address': 1610719244}
12:41:19.726 response READ_REG 00000000
12:41:19.727 request READ_REG {'address': 1610719244}
12:41:19.729 response READ_REG 00000000
12:41:19.731 request READ_REG {'address': 1610719248}
12:41:19.733 response READ_REG 000000
12:41:19.734 request READ_REG {'address': 1610719256}
12:41:19.737 response READ_REG 00000000
12:41:19.738 request READ_REG {'address': 1610719240}
12:41:19.740 response READ_REG 00000000
12:41:19.742 request READ_REG {'address': 1610719236}
12:41:19.744 response READ_REG 00000000
12:41:19.745 request MEM_BEGIN {'size': 3140, 'blocks': 1, 'blocksize': 6144, 'offset': 1074393088}
12:41:19.748 response MEM_BEGIN 00000000
12:41:19.751 request MEM_DATA
12:41:20.035 response MEM_DATA 00000000
12:41:20.037 request MEM_BEGIN {'size': 4, 'blocks': 1, 'blocksize': 6144, 'offset': 1073736612}
12:41:20.040 response MEM_BEGIN 00000000
12:41:20.041 request MEM_DATA
12:41:20.045 response MEM_DATA 00000000
12:41:20.046 request MEM_END {'flag': 0, 'entry': 1074394468}
12:41:20.048 response MEM_END 00000000
12:41:20.051 response !UNKNOWN COMMAND!: OHAI
12:41:20.052 request READ_REG {'address': 1610620956}
12:41:20.055 response READ_REG 0000
12:41:20.056 request READ_REG {'address': 1610620964}
12:41:20.058 response READ_REG 0000
12:41:20.059 request WRITE_REG {'address': 1610620972, 'value': 23, 'mask': 4294967295, 'delay': 0}
12:41:20.062 response WRITE_REG 0000
12:41:20.063 request WRITE_REG {'address': 1610620956, 'value': 2415919104, 'mask': 4294967295, 'delay': 0}
12:41:20.066 response WRITE_REG 0000
12:41:20.067 request WRITE_REG {'address': 1610620964, 'value': 1879048351, 'mask': 4294967295, 'delay': 0}
12:41:20.070 response WRITE_REG 0000
12:41:20.071 request WRITE_REG {'address': 1610621056, 'value': 0, 'mask': 4294967295, 'delay': 0}
12:41:20.074 response WRITE_REG 0000
12:41:20.075 request WRITE_REG {'address': 1610620928, 'value': 262144, 'mask': 4294967295, 'delay': 0}
12:41:20.078 response WRITE_REG 0000
12:41:20.079 request READ_REG {'address': 1610620928}
12:41:20.081 response READ_REG 0000
12:41:20.083 request READ_REG {'address': 1610621056}
12:41:20.085 response READ_REG 0000
12:41:20.086 request WRITE_REG {'address': 1610620956, 'value': 2147483712, 'mask': 4294967295, 'delay': 0}
12:41:20.089 response WRITE_REG 0000
12:41:20.090 request WRITE_REG {'address': 1610620964, 'value': 1879048192, 'mask': 4294967295, 'delay': 0}
12:41:20.093 response WRITE_REG 0000
12:41:20.094 request SPI_SET_PARAMS {'id': 0, 'total_size': 4194304, 'block_size': 65536, 'sector_size': 4096, 'page_size': 256, 'status_mask': 65535}
12:41:20.098 response SPI_SET_PARAMS 0000
12:41:20.099 request FLASH_DEFL_BEGIN {'write_size': 8192, 'num_blocks': 1, 'pagesize': 16384, 'offset': 57344}
12:41:20.103 response FLASH_DEFL_BEGIN 0000
12:41:20.104 request FLASH_DEFL_DATA
12:41:20.111 response FLASH_DEFL_DATA 0000
12:41:20.113 request SPI_FLASH_MD5
12:41:20.213 response SPI_FLASH_MD5 e6327541e2dc394ca2c3b3280adbdcf39f0000
12:41:20.229 request FLASH_DEFL_BEGIN {'write_size': 15856, 'num_blocks': 1, 'pagesize': 16384, 'offset': 4096}
12:41:20.233 response FLASH_DEFL_BEGIN 0000
12:41:20.237 request FLASH_DEFL_DATA
12:41:21.141 response FLASH_DEFL_DATA 0000
12:41:21.145 request SPI_FLASH_MD5
12:41:21.380 response SPI_FLASH_MD5 66ba7fa3a11e53e48ecfacb2319920040000
12:41:21.433 request FLASH_DEFL_BEGIN {'write_size': 219120, 'num_blocks': 7, 'pagesize': 16384, 'offset': 65536}
12:41:21.436 response FLASH_DEFL_BEGIN 0000
12:41:21.440 request FLASH_DEFL_DATA
12:41:22.878 response FLASH_DEFL_DATA 0000
12:41:22.890 request FLASH_DEFL_DATA
12:41:24.331 response FLASH_DEFL_DATA 0000
12:41:24.343 request FLASH_DEFL_DATA
12:41:25.785 response FLASH_DEFL_DATA 0000
12:41:25.796 request FLASH_DEFL_DATA
12:41:27.236 response FLASH_DEFL_DATA 0000
12:41:27.247 request FLASH_DEFL_DATA
12:41:28.686 response FLASH_DEFL_DATA 0000
12:41:28.697 request FLASH_DEFL_DATA
12:41:30.137 response FLASH_DEFL_DATA 0000
12:41:30.148 request FLASH_DEFL_DATA
12:41:31.400 response FLASH_DEFL_DATA 0000
12:41:31.403 request SPI_FLASH_MD5
12:41:31.511 response SPI_FLASH_MD5 ddd709af6de8d5533c43f7229783c5840000
12:41:31.802 request FLASH_DEFL_BEGIN {'write_size': 3072, 'num_blocks': 1, 'pagesize': 16384, 'offset': 32768}
12:41:31.805 response FLASH_DEFL_BEGIN 0000
12:41:31.806 request FLASH_DEFL_DATA
12:41:31.821 response FLASH_DEFL_DATA 0000
12:41:31.822 request SPI_FLASH_MD5
12:41:31.870 response SPI_FLASH_MD5 b3a1040c8763614dc1f6386bd9d0f0be0000
12:41:31.876 request FLASH_BEGIN {'size': 0, 'blocks': 0, 'blocksize': 16384, 'offset': 0}
12:41:31.880 response FLASH_BEGIN 0000
12:41:31.881 request FLASH_DEFL_END
12:41:31.883 response FLASH_DEFL_END
```

## :keyboard: ZX Spectrum Video Memory Emulation

Used to convert images from/to ZX Spectrum video memory dump.

### Usage

Command-line help:
```sh
python3 zxspectrum_video_memory.py -h
usage: zxspectrum_video_memory.py [-h] {s,w,m,c} ...

ZX Spectrum video utility. It allow import/export image from/to file

positional arguments:
  {s,w,m,c}   choose subcomand to run
    s         run speed test to calculate "get image" operations per second
    w         generate "Hello World" labels with random colors and save to
              image file
    m         load test data into video memory
    c         convert image with ZX video subsystem; image must have size
              256x192 pixels

optional arguments:
  -h, --help  show this help message and exit
```

Speed tests for cpython & pypy:
```sh
python3 zxspectrum_video_memory.py s
3.8.5 (default, Jul 28 2020, 12:59:40) 
[GCC 9.3.0]
avg=0.027 s/image; 36.7 images/s

pypy3 zxspectrum_video_memory.py s
3.6.12 (db1e853f94de, Nov 18 2020, 09:49:19)
[PyPy 7.3.3 with GCC 7.3.1 20180303 (Red Hat 7.3.1-5)]
avg=0.002 s/image; 627.0 images/s
```

Generates `hello_world.png` then import it into video memory and export to `hello_world_zx.png`:
```sh
python zxspectrum_video_memory.py w -l
```

Converts jpeg image according to ZX Spectrum video subsystem facility:
```sh
python3 zxspectrum_video_memory.py c -f stalker-poster.jpeg -s stalker-poster.png
```

### So, look examples:

Source image | ZX Spectrum video
------------ | -------------
![](/images/hello_world.png)      | ![](/images/hello_world_zx.png)
![](/images/stalker_ico.webp)     | ![](/images/stalker_ico.png)
![](/images/stalker_poster.jpeg)  | ![](/images/stalker_poster.png)


And would you like to went the Zone on ZX Spectrum ?.. :robot:
