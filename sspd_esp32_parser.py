#!/usr/bin/env python3

''' SLIP packets & ESP32 commands parser
	Autor: Viktoria Danchenko
	Used to pipe log data from sspd & dump SLIP packets.

	Examples.

	Log data from CP210x UART Bridge & dump SLIP packets:
	./sspd -tu 10c4:ea60 -b 115200 | python sspd_esp32_parser.py

	Log RX & TX UART lines from two CP210x UART Bridges & dump request/response SLIP packets to one log:
	parallel -j2 -- './sspd -tu 10c4:ea60 -b 115200 | python sspd_esp32_parser.py' './sspd -tu 10c4:ea60 -b 115200 | python sspd_esp32_parser.py'
'''

import sys
import re
import struct

commands = {
	# Supported by software loader and ROM loaders
	0x02: ('FLASH_BEGIN', '<IIII', ('size', 'blocks', 'blocksize', 'offset'))
	, 0x03: ('FLASH_DATA', '<II', ('size', 'sequence'))
	, 0x04: ('FLASH_END', '<IIII', ('stay',))
	, 0x05: ('MEM_BEGIN', '<IIII', ('size', 'blocks', 'blocksize', 'offset'))
	, 0x06: ('MEM_END', '<II', ('flag', 'entry'))
	, 0x07: ('MEM_DATA', '<II', ('size', 'sequence'))
	, 0x08: 'SYNC'
	, 0x09: ('WRITE_REG', '<IIII', ('address', 'value', 'mask', 'delay'))
	, 0x0A: ('READ_REG', '<I', ('address',))
	# Supported by software loader and ESP32 ROM Loader
	, 0x0B: ('SPI_SET_PARAMS', '<IIIIII', ('id', 'total_size', 'block_size', 'sector_size', 'page_size', 'status_mask'))
	, 0x0D: ('SPI_ATTACH', '<I', ('param',))
	, 0x0F: ('CHANGE_BAUDRATE', '<I', ('baud',))
	, 0x10: 'FLASH_DEFL_BEGIN', 0x11: 'FLASH_DEFL_DATA', 0x12: 'FLASH_DEFL_END'
	, 0x13: ('SPI_FLASH_MD5', '<II', ('address', 'size'))
	# upported by software loader only (ESP8266 & ESP32)
	, 0xD0: 'ERASE_FLASH'
	, 0xD1: ('ERASE_REGION', '<II', ('offset', 'size'))
	, 0xD2: ('READ_FLASH', '<IIII', ('offset', 'size', 'sectorsize', 'packetsize'))
	, 0xD3: 'RUN_USER_CODE'
	}

# match: 0 - timestamp, 1 - C-style escaped data
pattern = re.compile(r'(\d{2}:\d{2}:\d{2}.\d{3})\s+\d+[\s<>]+(.*)')

buff = b''
packet_start_timestamp: str = ''

def unescape(buff: str) -> bytearray:
	ret = b''
	i = 0
	while i < len(buff):
		if buff[i] == '\\' and len(buff) > i:
			# start escape sequence
			i += 1
			if buff[i] == 'x' and len(buff) > i + 1:
				# hex escape
				i += 1
				ret += bytes([int(buff[i:i+2], base=16)])
				i += 2
			else:
				if buff[i].isdigit():
					# octal escape
					ii = i + 1
					while ii - i < 3 and ii < len(buff) and buff[ii] in '01234567':
						ii += 1
					ret += bytes([int(buff[i:ii], base=8)])
					i = ii
				else:
					# named escape
					named_escape_index = 'abefnrtv\\'.find(buff[i])
					if named_escape_index < 0:
						# unknown escape
						print('unknown escape')
					else:
						ret += bytes('\x07\x08\x1B\x0C\x0A\x0D\x09\x0B\\'[named_escape_index], 'ascii')
					i += 1
		else:
			ret += bytes(buff[i], 'ascii')
			i += 1
	return ret

def parse_packet(buff: bytearray, timestamp: str=''):
	'Parses SLIP packet'
	# print('PACKET: ', buff)
	if len(buff) > 0:
		if timestamp:
			print(timestamp+' ', end='')
		print('request' if buff[0] == 0 else 'response', end='')
		if len(buff) > 1:
			if buff[1] in commands:
				cmd = commands[buff[1]]
				if isinstance(cmd, str):
					print(' '+cmd, end='')
				else:
					print(' '+cmd[0], end='')
					if buff[0] == 0:
						try:
							print(' '+str(dict(zip(cmd[2], struct.unpack(cmd[1], buff[8:])))), end='')
						except:
							pass
			else:
				print(' !UNKNOWN COMMAND!: '+str(buff)[2:-1], end='')
		print()

def parse_log_line(line: str):
	'Collects data from log strings & tries parse as SLIP packet sequence'
	global buff, packet_start_timestamp
	# split timestamp & data
	match = pattern.findall(line)
	if match:
		timestamp = match[0][0]
		# print(timestamp)
		buff += unescape(match[0][1])
		# try detect packet
		packet_start_index = buff.find(b'\xC0')
		while packet_start_index >= 0:
			if packet_start_index > 0:
				print('Skip {} bytes: {}'.format(packet_start_index, str(buff[:packet_start_index])[2:-1]))
			if not packet_start_timestamp:
				packet_start_timestamp = timestamp
			packet_end_index = buff.find(b'\xC0', packet_start_index + 1)
			if packet_end_index > 0:
				parse_packet(buff[packet_start_index+1:packet_end_index], packet_start_timestamp)
				buff = buff[packet_end_index+1:] # remove processed packed
				packet_start_timestamp = ''
			else:
				# not entire packet
				break
			packet_start_index = buff.find(b'\xC0')

while True:
	# detect match packet
	try:
		lines = input()
		for line in lines.splitlines():
			parse_log_line(line)
	except EOFError:
		break
