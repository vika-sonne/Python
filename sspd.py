#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#	Simple serial port dump
#	Copyright (C) Victoria Danchenko, 2018.
#
# Released under a MIT license, see LICENCE.txt.

import sys, traceback
from datetime import datetime, timedelta
import serial
import serial.tools.list_ports
import time
import argparse


VERBOSE_LEVEL = 0

def dump(message, level=0, datetime_stamp=False, ignore_verbose_level=False):
	if VERBOSE_LEVEL < level and not ignore_verbose_level:
		return
	if datetime_stamp:
		print(datetime.now().isoformat()+' '+'\t'*level+message)
	else:
		print(datetime.now().strftime('%H:%M:%S.%f ')+'\t'*level+message)

def dump_rcv(buff, message='', level=0):
	if VERBOSE_LEVEL < level:
		return
	if len(message) > 0:
		print(datetime.now().strftime('%H:%M:%S.%f ')+'{:02}'.format(len(buff))+'\t'*level+' >> '
			+message+': '+str(buff.decode('latin').encode('ascii', 'backslashreplace'))[2:-1])
	else:
		print(datetime.now().strftime('%H:%M:%S.%f ')+'{:02}'.format(len(buff))+'\t'*level+' >> '
			+str(buff.decode('latin').encode('ascii', 'backslashreplace'))[2:-1])

def dump_snd(buff, message='', level=0):
	if VERBOSE_LEVEL < level:
		return
	if len(message) > 0:
		print(datetime.now().strftime('%H:%M:%S.%f')+'{:02}'.format(len(buff))+'\t'*level+' << '
			+message+': '+str(buff.decode('latin').encode('ascii', 'backslashreplace'))[2:-1])
	else:
		print(datetime.now().strftime('%H:%M:%S.%f')+'{:02}'.format(len(buff))+'\t'*level+' << '
			+str(buff.decode('latin').encode('ascii', 'backslashreplace'))[2:-1])

DEFAULT_COM_PORT = 'COM1' if sys.platform.startswith('win') else 'ttyUSB0'
DEFAULT_COM_BAUDRATE = 115200
DEFAULT_COM_RECONNECT_DELAY = 2.0
COM_SCAN_PERIOD = .5 # seconds

def pase_args():
	parser = argparse.ArgumentParser(description='Simple serial port dump', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-p', '--port', metavar='COM_PORT', default=DEFAULT_COM_PORT,
		help='serial port; default: '+str(DEFAULT_COM_PORT))
	parser.add_argument('-b', '--baudrate', metavar='BAUDRATE', default=DEFAULT_COM_BAUDRATE, type=int,
		help='serial port baudrate; default: '+str(DEFAULT_COM_BAUDRATE))
	parser.add_argument('-v', action='count', default=0, help='verbose level: -v, -vv or -vvv (bytes); default: -v')
	parser.add_argument('-r', action='store_true', help='reconnect to serial port')
	parser.add_argument('--bytes', action='store_true', help='receive byte by byte')
	parser.add_argument('--reconnect-delay', metavar='SEC', type=float, default=DEFAULT_COM_RECONNECT_DELAY,
		help='reconnect delay, s; default: '+str(DEFAULT_COM_RECONNECT_DELAY))
	parser.add_argument('--vid-pid', metavar='VID:PID',
		help='search for USB: VendorID:ProductID[,VendorID:ProductID[...]]; example: 03eb:2404,03eb:6124')
	parser.add_argument('--trace-error', action='store_true', help='show the errors trace; default: off')
	args = parser.parse_args()
	VERBOSE_LEVEL = args.v
	if VERBOSE_LEVEL > 0:
		dump('arguments:', ignore_verbose_level=True)
		for attribute, value in sorted(args.__dict__.items()):
			def is_numeric(v):
				return type(v) in [int, float]
			dump(('--' if len(attribute)>1 else '-')+
				attribute.replace('_','-')+
				'='+('' if is_numeric(value) else '"')+
				str(value)+('' if is_numeric(value) else '"'), ignore_verbose_level=True)
	return args

args = pase_args()

dump('START', datetime_stamp=True)

if not sys.platform.startswith('win') and args.port.find('/') < 0:
	args.port = '/dev/'+args.port

def port_dump(show_connect_message=True, show_connect_error_message=True):
	if show_connect_message:
		dump('Open serial port: {} @ {} 8N1'.format(args.port, args.baudrate))
	port = None
	try:
		port = serial.Serial(
			port=args.port,
			baudrate=args.baudrate,
			timeout=2,
			bytesize=serial.EIGHTBITS,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE)
	except Exception as e:
		if show_connect_error_message or args.trace_error:
			print(u'ERROR: '+str(e))
			if args.trace_error:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, file=sys.stderr)
	else:
		try:
			if not port.is_open:
				port.open()
			while True:
				if args.bytes:
					buff = port.read()
				else:
					buff = port.readline()
				if len(buff) > 0:
					dump_rcv(buff)
				else:
					return
		except Exception as e:
			print(u'ERROR: '+str(e))
			if args.trace_error:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, file=sys.stderr)

	if port and port.isOpen():
		port.close()
	del port

def autoconnect():
	'Waits until USB device connected'
	if type(args.vid_pid) == str:
		vidpids = []
		for vid_pid in args.vid_pid.split(','):
			vid_pid = vid_pid.split(':')
			if len(vid_pid) != 2:
				raise Exception('Error parsing USB VID:PID: "{}"'.format(args.vid_pid))
			vidpids.append((int(vid_pid[0], 16), int(vid_pid[1], 16)))
		args.vid_pid = vidpids
	while True:
		for p in serial.tools.list_ports.comports():
			for vid_pid in args.vid_pid:
				if vid_pid[0] == p.vid and vid_pid[1] == p.pid:
					args.port = p.device
					print('Found USB: {:04X}:{:04X} {}'.format(p.vid, p.pid, p.device))
					return
		time.sleep(COM_SCAN_PERIOD)

def main():

	if args.vid_pid:
		autoconnect() # scan USB devices & wait

	if args.r:
		show_connect_message = True
		while True:
			port_dump(show_connect_message=show_connect_message, show_connect_error_message=False)
			time.sleep(args.reconnect_delay)
			if args.vid_pid:
				show_connect_message = True
				autoconnect() # scan USB devices & wait
			else:
				show_connect_message = False
	else:
		port_dump()


try:
	main()
except KeyboardInterrupt:
	sys.exit(-1)
