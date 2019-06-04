#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#	Converts file as binary blob to C/C++ header as array
#	Copyright (C) Victoria Danchenko, 2019.
#
# Released under a MIT license, see LICENCE.txt.


from os import path
import argparse


DEFAULT_ARRAY_DECLARATION = 'unsigned char binary_blob'

def pase_args():
	parser = argparse.ArgumentParser(description='Converts file as binary blob to C/C++ header as array', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-i', metavar='INPUT_FILEPATH', required=True)
	parser.add_argument('-o', metavar='OUTPUT_FILEPATH',
		help='if omitted writes to console')
	parser.add_argument('-d', metavar='ARRAY_DECLARATION', default=DEFAULT_ARRAY_DECLARATION,
		help='array declaration; default: "{}"'.format(DEFAULT_ARRAY_DECLARATION))
	args = parser.parse_args()
	return args

args = pase_args()

def convert(fin, fout):
	fout.write('%s[%s] = {\n' % (args.d, path.getsize(args.i)))
	buff = fin.read(16)
	is_first_line = True
	while buff:
		if not is_first_line:
			fout.write(',\n')
		fout.write(', '.join([ '0x{:X}'.format(x) for x in buff ]))
		buff = fin.read(16)
		is_first_line = False
	fout.write('\n};\n')

with open(args.i, 'rb') as fin: # input file
	if args.o:
		# output to file
		with open(args.o, 'w') as fout:
			convert(fin, fout)
	else:
		# output to console
		import sys
		convert(fin, sys.stdout)
