#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Atmel Studio Project file Converter

import sys
import datetime
import os
from lxml import etree
import argparse
from typing import List


class AtmelStudioCProjectFile():
	"Atmel Studio Project file Converter"

	NAMESPACE_MSBUILD_2003 = 'http://schemas.microsoft.com/developer/msbuild/2003'

	@staticmethod
	def unescape(text):
		while True:
			escape_index = text.find('%')
			if escape_index < 0:
				return text
			text = text[:escape_index] + chr(int(text[escape_index+1:escape_index+3], 16)) + text[escape_index+3:]

	class Condition():
		def __init__(self, condition=''):
			self.condition = condition
			self.defines, self.include_paths = [], []
			self.compiler_optimization, self.compiler_debug_level, self.compiler_other_flags = '', '', ''
			self.assembler_flags = ''
			self.linker_libraries, self.linker_library_search_paths, self.linker_flags = [], [], ''

	def __init__(self, project_file_path):

		def get_subelement_text(parent_element, subelement_name) -> str:
			subelement = parent_element.xpath('x:{}'.format(subelement_name), namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003})
			return AtmelStudioCProjectFile.unescape(subelement[0].text) if subelement else ''

		def get_subelements_list_texts(parent_element, subelement_name: str, prefix='') -> List[str]:
			subelement_list = parent_element.xpath('x:{}/x:ListValues/*'.format(subelement_name), namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003})
			return [ prefix+AtmelStudioCProjectFile.unescape(i.text) for i in subelement_list ] if subelement_list else []

		self.name, self.device = '', ''
		self.files, self.exclude_files, = [], []
		self.conditions = []
		with open(project_file_path, 'r') as project_file:
			root = etree.fromstring(project_file.read())
			for property_group in root.xpath('x:PropertyGroup', namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003}):
				if 'Condition' in property_group.attrib:
					condition = AtmelStudioCProjectFile.Condition(property_group.attrib['Condition'].strip())
					arm_gcc = property_group.xpath('x:ToolchainSettings/x:ArmGcc', namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003})
					if arm_gcc:
						arm_gcc = arm_gcc[0]
						condition.defines = get_subelements_list_texts(arm_gcc, 'armgcc.compiler.symbols.DefSymbols')
						condition.include_paths = get_subelements_list_texts(arm_gcc, 'armgcc.compiler.directories.IncludePaths')
						condition.compiler_optimization = get_subelement_text(arm_gcc, 'armgcc.compiler.optimization.level')
						condition.compiler_other_flags = ' '.join([ get_subelement_text(arm_gcc, 'armgcc.compiler.optimization.OtherFlags'), get_subelement_text(arm_gcc, 'armgcc.compiler.miscellaneous.OtherFlags') ] )
						condition.compiler_debug_level = get_subelement_text(arm_gcc, 'armgcc.compiler.optimization.DebugLevel')
						condition.assembler_flags = get_subelement_text(arm_gcc, 'armgcc.preprocessingassembler.general.AssemblerFlags')
						condition.linker_libraries = get_subelements_list_texts(arm_gcc, 'armgcc.linker.libraries.Libraries')
						condition.linker_library_search_paths = get_subelements_list_texts(arm_gcc, 'armgcc.linker.libraries.LibrarySearchPaths')
						condition.linker_flags = get_subelement_text(arm_gcc, 'armgcc.linker.miscellaneous.LinkerFlags')+' '+' '.join(get_subelements_list_texts(arm_gcc, 'armgcc.linker.miscellaneous.OtherOptions', '-Xlinker '))
						self.conditions.append(condition)
				else:
					self.name = get_subelement_text(property_group, 'Name')
					self.device = get_subelement_text(property_group, 'avrdevice')
					# for project_file in property_group.xpath('x:AsfFrameworkConfig/x:framework-data/x:files/*', namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003}):
					# 	self.files.append(project_file.attrib['path'])
			for item_group in root.xpath('x:ItemGroup/x:Compile', namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003}):
				self.files.append(item_group.attrib['Include'])
			for item_group in root.xpath('x:ItemGroup/x:None', namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003}):
				self.exclude_files.append(item_group.attrib['Include'])

	def __str__(self):
		def condition_str(condition):
			return 'condition: "{}"; defines: "{}"; compiler_optimization: "{}"; compiler_other_flags: "{}"; compiler_debug_level: "{}"; linker_libraries: "{}"; linker_library_search_paths: "{}"; linker_flags: "{}"; include_paths: "{}"'.format(
				condition.condition, '", "'.join(condition.defines), condition.compiler_optimization, condition.compiler_other_flags, condition.compiler_debug_level, '", "'.join(condition.linker_libraries), '", "'.join(condition.linker_library_search_paths), condition.linker_flags, '", "'.join(condition.include_paths))
		ret = 'Project: "{}"; device: "{}"; files: "{}"; exclude_files: "{}"'.format(
				self.name, self.device, '", "'.join(self.files), '", "'.join(self.exclude_files))
		for condition in self.conditions:
			ret += '; '+condition_str(condition)
		return ret


def normalize_path(text):
	def convert_variable_usage(text):
		while True:
			variable_index = text.find('$(')
			if variable_index < 0:
				break
			text = text[:variable_index+1] + '{' + text[variable_index+2:]
			variable_index = text.find(')', variable_index)
			if variable_index < 0:
				break
			text = text[:variable_index] + '}' + text[variable_index+1:]
		return text
	text = convert_variable_usage(text)
	if sys.platform.startswith('win'):
		text = text.replace('/', '\\') # linux paths separator to windows
	else:
		text = text.replace('\\', '/') # windows paths separator to linux
	return text

def print_eclipse_cdt_includes_and_symbols_xml(cproject: AtmelStudioCProjectFile, condition: AtmelStudioCProjectFile.Condition):

	def write_section(name, languages, texts):
		print(('\t<section name="{}">\n').format(name))
		for i in languages:
			print(('\t\t<language name="{}">\n').format(i))
			for ii in texts:
				print(('\t\t\t{}\n').format(ii))
			print('\t\t</language>\n')
		print('\t</section>\n')

	def remove_prefix(text, prefix):
		if prefix and text.startswith(prefix):
			text = text[len(prefix):]
		return text

	print(('<?xml version="1.0" encoding="UTF-8"?>\n<!-- {} This is auto-generated file from Atmel Studio project "{}", device "{}", condition "{}" -->\n').format(datetime.datetime.now().isoformat(), cproject.name, cproject.device, condition.condition))
	print('<cdtprojectproperties>\n')
	LANGUAGES = [ 'Assembly Source File', 'C Source File' ]
	write_section(
		'org.eclipse.cdt.internal.ui.wizards.settingswizards.IncludePaths',
		LANGUAGES,
		[ '<includepath>{}</includepath>'.format(normalize_path(remove_prefix(i, args.include_path_remove_prefix))) if '$' in i else '<includepath workspace_path="true">{}</includepath>'.format(normalize_path(remove_prefix(i, args.include_path_remove_prefix))) for i in condition.include_paths ]
		)
	write_section(
		'org.eclipse.cdt.internal.ui.wizards.settingswizards.Macros',
		LANGUAGES,
		[ '<macro><name>{0[0]}</name><value>{0[2]}</value></macro>'.format(i.partition('=')) if '=' in i else '<macro><name>{}</name><value/></macro>'.format(i) for i in condition.defines ]
		)
	print('</cdtprojectproperties>\n')

if __name__ == "__main__":

	def parse_args():
		parser = argparse.ArgumentParser(
			description='Atmel Studio Project conversion',
			formatter_class=argparse.RawTextHelpFormatter,
			epilog='Copyright (C) Victoria Danchenko, 2019.')

		parser.add_argument('-v', action='count', default=0, help='verbose level: -v; default: no verbose')
		parser.add_argument('-p', '--project-file', required=True, help='Atmel Studio project file path')

		subparsers = parser.add_subparsers(dest='cmd')

		parser_info = subparsers.add_parser('info', help='print the Atmel Studio project information')
		parser_info.add_argument('kind', choices=['conditions', 'include', 'exclude', 'defines'])
		del parser_info

		parser_htm = subparsers.add_parser('htm', help='print the html report')
		del parser_htm

		parser_eclipse = subparsers.add_parser('eclipse', help='export to Eclipse CDT project')
		eclipse_parser = parser_eclipse.add_subparsers(dest='cmd_eclipse', help='export to Eclipse CDT project')
		parser_include_and_symbols = eclipse_parser.add_parser('include-and-symbols', \
			help='print Eclipse settings xml file to import to CDT project on "C/C++ General/Path and Symbols" tab of project properties. Contains xml tag <cdtprojectproperties>')
		parser_include_and_symbols.add_argument('-c', '--condition', required=True, help='name of Atmel Studio Project build condition')
		parser_include_and_symbols.add_argument('--include-path-remove-prefix')
		parser_include_and_symbols = eclipse_parser.add_parser('excluding', \
			help='print Eclipse CDT project excluding files. Contains part of CDT project file: two xml tags <sourceEntries><entry excluding="..."></sourceEntries>')
		del parser_eclipse

		parser_sh = subparsers.add_parser('sh', help='export to build shell script')
		parser_sh.add_argument('-c', '--condition', required=True, help='name of Atmel Studio Project build condition')
		parser_sh.add_argument('--toolchain-prefix', metavar='PREFIX', default='arm-none-eabi-', help='toolchain excecutables file name prefix; default: arm-none-eabi-')
		parser_sh.add_argument('--toolchain-suffix', metavar='SUFFIX', default='', help='toolchain excecutables file name suffix')
		parser_sh.add_argument('--cflags', default='', help='C compiler flags')
		parser_sh.add_argument('--ldflags', default='', help='linker flags')
		parser_sh.add_argument('--toolchain-path', metavar='PATH', default='', help='path to toolchain excecutables; example: /opt/gcc-arm-none-eabi-4_8-2014q3/bin')
		parser_sh.add_argument('--target-file', default='a.out', help='Target file; example: target.elf')
		del parser_sh

		args = parser.parse_args()
		VERBOSE_LEVEL = args.v
		if VERBOSE_LEVEL > 0:
			print('arguments:')
			for attribute, value in sorted(args.__dict__.items()):
				def is_numeric(v):
					return type(v) in [int, float]
				print(('\t--' if len(attribute)>1 else '\t-')+
					attribute.replace('_','-')+
					'='+('' if is_numeric(value) else '"')+
					str(value)+('' if is_numeric(value) else '"'))
		return args

	def escape_path(path):
		return "".join(x for x in path if (x.isalnum() or x in "._-()[]{}+-'= "))

	args = parse_args()

	cproject = AtmelStudioCProjectFile(args.project_file)

	if args.cmd == 'info':
		if args.kind == 'conditions':
			for condition in cproject.conditions:
				print(condition.condition)
		elif args.kind == 'include':
			for condition in cproject.conditions:
				print()
				print(condition.condition)
				for f in sorted(condition.include_paths):
					print(f)
		elif args.kind == 'exclude':
			for exclude_file in sorted(cproject.exclude_files):
				print(exclude_file)
		elif args.kind == 'defines':
			for condition in cproject.conditions:
				print()
				print(condition.condition)
				for define in sorted(condition.defines):
					print(define)

	elif args.cmd == 'htm':
		# print the html
		print('<html>\n\t<body>')
		# project info
		print(('\t\t<h1>Atmel Studio project file export</h1>\n\t\t<table frame="border" cellpadding="5"><tr><td>Date &amp; time</td><td>{}</td></tr>\n\t\t<tr><td>Name</td><td>{}</td></tr>\n\t\t<tr><td>Device</td><td>{}</td></tr></table>').format(datetime.datetime.now().isoformat(), cproject.name, cproject.device))
		# content table
		print('<hr/><h2>Table of contents</h2>')
		for condition_index, condition in enumerate(cproject.conditions):
			print('<p><a href="#'+str(condition_index+1)+'">'+str(condition_index+1)+'. '+condition.condition+'</a></p>')
		print('<p><a href="#'+str(len(cproject.conditions)+1)+'">'+str(len(cproject.conditions)+1)+'. Files</a></p>')
		print('<p><a href="#'+str(len(cproject.conditions)+2)+'">'+str(len(cproject.conditions)+2)+'. Exclude files</a></p>')
		# conditions
		for condition_index, condition in enumerate(cproject.conditions):
			print('<hr/><h2 id="'+str(condition_index+1)+'">'+str(condition_index+1)+'. '+condition.condition+'</h2>')
			# defines
			print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.1. Defines</h3></caption>')
			for i, f in enumerate(sorted(condition.defines)):
				print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
			print('</table>')
			# compiler
			print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.2. Compiler</h3></caption>')
			print('<tr><td>Optimization</td><td>'+condition.compiler_optimization+'</td></tr>')
			print('<tr><td>Debug level</td><td>'+condition.compiler_debug_level+'</td></tr>')
			print('<tr><td>Other flags</td><td>'+condition.compiler_other_flags+'</td></tr>')
			print('</table>')
			# assembler
			print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.3. Assembler</h3></caption>')
			print('<tr><td>Flags</td><td>'+condition.assembler_flags+'</td></tr>')
			print('</table>')
			# linker
			print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.4. Linker</h3></caption>')
			for i, f in enumerate(sorted(condition.linker_libraries)):
				print('<tr><td>'+('Libraries' if i==0 else '')+'</td><td>'+f+'</td></tr>')
			for i, f in enumerate(sorted(condition.linker_library_search_paths)):
				print('<tr><td>'+('Library search path' if i==0 else '')+'</td><td>'+f+'</td></tr>')
			print('<tr><td>Other flags</td><td>'+condition.linker_flags+'</td></tr>')
			print('</table>')
			# include paths
			print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.5. Include paths</h3></caption>')
			for i, f in enumerate(sorted(condition.include_paths)):
				print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
			print('</table>')
		# files
		print('<hr/><table frame="border" cellpadding="5"><caption><h2 id="'+str(len(cproject.conditions)+1)+'" style="text-align:left">'+str(len(cproject.conditions)+1)+'. Files</h2></caption>')
		for i, f in enumerate(sorted(cproject.files)):
			print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
		print('</table>')
		# exclude files
		print('<hr/><table frame="border" cellpadding="5"><caption><h2 id="'+str(len(cproject.conditions)+2)+'" style="text-align:left">'+str(len(cproject.conditions)+2)+'. Exclude files</h2></caption>')
		for i, f in enumerate(sorted(cproject.exclude_files)):
			print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
		print('</table>')
		print('\t</body>\n</html>')
		# print(str(cproject))

	elif args.cmd == 'eclipse':

		if args.cmd_eclipse == 'include-and-symbols':
			for condition in cproject.conditions:
				if condition.condition == args.condition:
					print_eclipse_cdt_includes_and_symbols_xml(cproject, condition)
					break

		if args.cmd_eclipse == 'excluding':
			print('<sourceEntries>\n\t<entry excluding="'+'|'.join(cproject.exclude_files)+'" flags="VALUE_WORKSPACE_PATH" kind="sourcePath" name=""/>\n</sourceEntries>')

	elif args.cmd == 'sh':

		for condition in cproject.conditions:
			if condition.condition == args.condition:
				# print(condition.compiler_optimization)
				# print(condition.compiler_debug_level)
				print(f'''#!/usr/bin/env sh

# This file created by ASPC automation {os.path.basename(sys.argv[0])}
# Date time: {datetime.datetime.now().isoformat()}
# Atmel Studio project file: {args.project_file}
# command-line: {' '.join([('"'+x+'"' if ' ' in x else x) for x in sys.argv])}

date -Is

# C Compiler
CC={'"'+os.path.join(args.toolchain_path, args.toolchain_prefix+'gcc'+args.toolchain_suffix)+'"'}

# Linker
LD={'"'+os.path.join(args.toolchain_path, args.toolchain_prefix+'gcc'+args.toolchain_suffix)+'"'}

# C compiler FLAGS
CFLAGS="{' '.join(['-D'+x for x in condition.defines])} {condition.compiler_other_flags} {' '.join(['-I'+normalize_path(x) for x in condition.include_paths])} {args.cflags}"

# Linker FLAGS
LDFLAGS="{' '.join(['-l'+(x[3:] if x.startswith('lib') else x) for x in condition.linker_libraries])} {' '.join(['-L'+normalize_path(x) for x in condition.linker_library_search_paths])} {condition.linker_flags} {args.ldflags}"

# Create necessary path tree
{os.linesep.join(sorted(set(['mkdir -p "'+os.path.dirname(normalize_path(x))+'"' for x in cproject.files if x.endswith('.c')])))}

# Remove target file
rm -vf {args.target_file}

# Run C Compiler
{os.linesep.join( ['echo '+normalize_path(x)+os.linesep+'$CC $CFLAGS -o "'+normalize_path(x)[:-2]+'.o" "../'+normalize_path(x)+'"' for x in cproject.files if x.endswith('.c')] )}

echo Link
$LD $LDFLAGS {' '.join(['"'+normalize_path(x)[:-2]+'.o"' for x in cproject.files if x.endswith('.c')])} -o {args.target_file}

if [ "$?" -eq 0 ]
then
	echo "Link OK"
else
	echo "Link FAIL"
fi

date -Is
''')
