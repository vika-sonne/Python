#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

#      Simple serial port dump
#     Copyright (C) Victoria Danchenko, 2018.
#
# Released under a MIT license, see LICENCE.txt.

import sys, traceback
from datetime import datetime, timedelta
import serial
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
		print(datetime.now().strftime('%H:%M:%S.%f ')+'{:02}'.format(len(buff))+'\t'*level+' >> '+message+': '+str(buff.decode('latin').encode('unicode_escape')))
	else:
		print(datetime.now().strftime('%H:%M:%S.%f ')+'{:02}'.format(len(buff))+'\t'*level+' >> '+str(buff.decode('latin').encode('unicode_escape')))

def dump_snd(buff, message='', level=0):
	if VERBOSE_LEVEL < level:
		return
	if len(message) > 0:
		print(datetime.now().strftime('%H:%M:%S.%f')+'{:02}'.format(len(buff))+'\t'*level+' << '+message+': '+str(buff.decode('latin').encode('unicode_escape')))
	else:
		print(datetime.now().strftime('%H:%M:%S.%f')+'{:02}'.format(len(buff))+'\t'*level+' << '+str(buff.decode('latin').encode('unicode_escape')))

DEFAULT_COM_PORT = 'COM1' if sys.platform.startswith('win') else 'ttyUSB0'
DEFAULT_COM_BAUDRATE = 115200
DEFAULT_COM_RECONNECT_DELAY = 2.0

def pase_args():
	parser = argparse.ArgumentParser(description='Simple serial port dump', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-p', '--port', metavar='COM_PORT', default=DEFAULT_COM_PORT,
		help='serial port; default: '+str(DEFAULT_COM_PORT))
	parser.add_argument('-b', '--baudrate', metavar='BAUDRATE', default=DEFAULT_COM_BAUDRATE, type=int,
		help='serial port baudrate; default: '+str(DEFAULT_COM_BAUDRATE))
	parser.add_argument('-v', action='count', default=0, help='verbose level: -v, -vv or -vvv (bytes); default: -v')
	parser.add_argument('-r', action='store_true', help='reconnect to serial port')
	parser.add_argument('--reconnect-delay', metavar='SEC', type=float, default=DEFAULT_COM_RECONNECT_DELAY,
		help='reconnect delay, s; default: '+str(DEFAULT_COM_RECONNECT_DELAY))
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

def port_dump(show_open_message=True):
	if show_open_message:
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
		if args.trace_error:
			print(u'ERROR: '+str(e))
	else:
		try:
			if not port.is_open:
				port.open()
			while True:
				buff = port.readline()
				if len(buff) > 0:
					dump_rcv(buff)
		except Exception as e:
			if args.trace_error:
				print(u'ERROR: '+str(e))
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, file=sys.stderr)
		except (KeyboardInterrupt, SystemExit):
			sys.exit(-1)

	if port and port.isOpen():
		port.close()
	del port

if args.r:
	show_open_message = True
	while True:
		port_dump(show_open_message)
		show_open_message = False
		time.sleep(args.reconnect_delay)
else:
	port_dump()
