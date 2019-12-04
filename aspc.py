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

# arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O1 -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -g3 -DARM_MATH_CM4=true -DBOARD=SAM4S_EK2 -D__SAM4SD16C__ -DMECC -DLTC_DER -DSHA256 -DLTC_SOURCE -DGMP_DESC -DRIJNDAEL -DOFB -DFORTUNA -DFORTUNA_POOLS=16 -DFORTUNA_WD=10 -DUDD_ENABLE -DNDEBUG -D__FPU_PRESENT=0 -DHB_STAGE4_TEST -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/boards -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/clock -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/gpio -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/ioport -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/utils -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/boards -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/pio -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/pmc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils/header_files -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils/preprocessor -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/CMSIS/Include -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/CMSIS/Lib/GCC -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/config -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/adc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/storage/ctrl_access -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/rtc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/spi -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/components/memory/sd_mmc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/delay -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/spi/sam_spi -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/spi -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/uart -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/usart -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/serial/sam_uart -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/serial -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/utils/stdio/stdio_serial -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/pwm -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/fatfs/fatfs-r0.09/src -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/fatfs/fatfs-port-r0.09/sam -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/pdc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/gpbr -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/supc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/dacc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/rstc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/efc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/services/flash_efc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/wdt -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/twi -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/twi -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/rtt -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/libtomcrypt/headers -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/minigmp -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/sleepmgr -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/usb -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/usb/class/cdc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/usb/class/cdc/device -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/services/usb/udc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/common/utils/stdio/stdio_usb -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/uotghs -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/hsmci -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils/cmsis/sam4s/include -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils/cmsis/sam4s/source/templates -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/boards/sam4s_ek2 -I/opt/gcc-arm-none-eabi-4_8-2014q3/bin//../../CMSIS_Atmel/Device/ATMEL/sam4s/include -I/opt/gcc-arm-none-eabi-4_8-2014q3/bin//../../CMSIS_Atmel -I/opt/gcc-arm-none-eabi-4_8-2014q3/bin//../../CMSIS_Atmel/CMSIS/Include -I/opt/gcc-arm-none-eabi-4_8-2014q3/bin//../../CMSIS_Atmel/Device/ATMEL -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/udp -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/drivers/tc -I/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/littlefs -include/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/hb_build_config.h -std=gnu11 -c -o src/libtomcrypt/pk/ecc/ltc_ecc_projective_add_point.o ../src/libtomcrypt/pk/ecc/ltc_ecc_projective_add_point.c 

# arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O1 -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -g3 -T /home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/sam/utils/linker_scripts/sam4s/sam4sd32/gcc/production.flash.ld -Xlinker --gc-sections -L/home/vika/eclipse-workspace2/hb_firmware_factory_tests/src/ASF/thirdparty/CMSIS/Lib/GCC -Wl,-Map,hb_firmware_factory_tests.map -o hb_firmware_factory_tests.elf src/ASF/common/components/memory/sd_mmc/sd_mmc.o src/ASF/common/components/memory/sd_mmc/sd_mmc_mem.o src/ASF/common/components/memory/sd_mmc/sd_mmc_spi.o src/ASF/common/services/clock/sam4s/sysclk.o src/ASF/common/services/delay/sam/cycle_counter.o src/ASF/common/services/serial/usart_serial.o src/ASF/common/services/sleepmgr/sam/sleepmgr.o src/ASF/common/services/spi/sam_spi/spi_master.o src/ASF/common/services/storage/ctrl_access/ctrl_access.o src/ASF/common/services/usb/class/cdc/device/udi_cdc.o src/ASF/common/services/usb/class/cdc/device/udi_cdc_desc.o src/ASF/common/services/usb/udc/udc.o src/ASF/common/utils/interrupt/interrupt_sam_nvic.o src/ASF/common/utils/stdio/read.o src/ASF/common/utils/stdio/stdio_usb/stdio_usb.o src/ASF/common/utils/stdio/write.o src/ASF/sam/boards/sam4s_ek2/init.o src/ASF/sam/boards/sam4s_ek2/led.o src/ASF/sam/drivers/adc/adc.o src/ASF/sam/drivers/adc/adc_sam3u.o src/ASF/sam/drivers/dacc/dacc.o src/ASF/sam/drivers/dmac/dmac.o src/ASF/sam/drivers/efc/efc.o src/ASF/sam/drivers/gpbr/gpbr.o src/ASF/sam/drivers/hsmci/hsmci.o src/ASF/sam/drivers/pdc/pdc.o src/ASF/sam/drivers/pio/pio.o src/ASF/sam/drivers/pio/pio_handler.o src/ASF/sam/drivers/pmc/pmc.o src/ASF/sam/drivers/pmc/sleep.o src/ASF/sam/drivers/pwm/pwm.o src/ASF/sam/drivers/rstc/rstc.o src/ASF/sam/drivers/rtc/rtc.o src/ASF/sam/drivers/rtt/rtt.o src/ASF/sam/drivers/spi/spi.o src/ASF/sam/drivers/supc/supc.o src/ASF/sam/drivers/tc/tc.o src/ASF/sam/drivers/trng/trng.o src/ASF/sam/drivers/twi/twi.o src/ASF/sam/drivers/uart/uart.o src/ASF/sam/drivers/udp/udp_device.o src/ASF/sam/drivers/uotghs/uotghs_device.o src/ASF/sam/drivers/usart/usart.o src/ASF/sam/drivers/wdt/wdt.o src/ASF/sam/services/flash_efc/flash_efc.o src/ASF/sam/utils/cmsis/sam4s/source/exceptions.o src/ASF/sam/utils/cmsis/sam4s/source/system_sam4s.o src/ASF/sam/utils/cmsis/sam4s/source/templates/gcc/startup_sam4s.o src/ASF/sam/utils/syscalls/gcc/syscalls.o src/ASF/thirdparty/fatfs/fatfs-port-r0.09/diskio.o src/ASF/thirdparty/fatfs/fatfs-port-r0.09/sam/fattime_rtc.o src/ASF/thirdparty/fatfs/fatfs-r0.09/src/ff.o src/ASF/thirdparty/littlefs/lfs.o src/ASF/thirdparty/littlefs/lfs_util.o "src/Core/Core Modules/IO/hb_core_io.o" src/Core/Loader/ble_prog/c2540prog.o src/Core/Loader/esp_prog/esp32_prog.o src/Core/Loader/hb_crypto.o src/Core/Loader/hb_developer.o src/Core/Loader/hb_incrc32.o src/Core/Loader/hb_incrypt.o src/Core/Loader/hb_inhash.o src/Core/Loader/hb_inprogress.o src/Core/Loader/hb_instream.o src/Core/Loader/hb_loader.o src/Core/Loader/hb_parse.o src/Core/Loader/hb_simplest.o src/Core/Loader/led_display_prog/hb_stk500_avr_prog.o src/Core/hb_DateTime.o src/Core/hb_ani_test.o src/Core/hb_battery.o src/Core/hb_core.o src/Core/hb_data_exchange.o src/Core/hb_display.o src/Core/hb_hal.o src/Core/hb_hal_display.o src/Core/hb_ipc.o src/Core/hb_logger.o src/Core/hb_metadata.o src/Core/hb_pulser.o src/Core/hb_storage.o src/Core/hb_sysdata.o src/Core/hb_sysdata_hl.o src/Core/hb_system_tick.o src/Core/hb_timers.o src/Core/hb_tsts_ipc.o src/CoreTest/hb_pcb_test.o src/CoreTest/hb_pw_tester.o src/CoreTest/hb_sinewave.o src/CoreTest/pw_samples.o src/HW/hw_adc.o src/HW/hw_afe44xx.o src/HW/hw_board.o src/HW/hw_bq27426.o src/HW/hw_gen_table.o src/HW/hw_gpio.o src/HW/hw_io_common.o src/HW/hw_pwm.o src/HW/hw_spi.o src/HW/hw_twi.o src/HW/hw_uart.o src/HW/hw_usart.o src/HW/hw_usb.o src/HW/hw_w25q.o src/HW/hw_w25q_mem.o src/Utils/hb_assert.o src/Utils/hb_bit_buffer_cnt.o src/Utils/hb_fifo.o src/Utils/hb_median.o src/Utils/hb_moving_average.o src/Utils/hb_trace.o src/Utils/hb_utils.o src/Utils/median.o src/cdc/cdc_other.o src/cdc/cdc_uart.o src/libtomcrypt/ciphers/aes/aes.o src/libtomcrypt/ciphers/des.o src/libtomcrypt/hashes/helper/hash_memory.o src/libtomcrypt/hashes/sha2/sha256.o src/libtomcrypt/math/gmp_desc.o src/libtomcrypt/math/multi.o src/libtomcrypt/math/rand_prime.o src/libtomcrypt/misc/crypt/crypt_cipher_descriptor.o src/libtomcrypt/misc/crypt/crypt_cipher_is_valid.o src/libtomcrypt/misc/crypt/crypt_find_cipher.o src/libtomcrypt/misc/crypt/crypt_find_hash.o src/libtomcrypt/misc/crypt/crypt_find_hash_id.o src/libtomcrypt/misc/crypt/crypt_find_hash_oid.o src/libtomcrypt/misc/crypt/crypt_find_prng.o src/libtomcrypt/misc/crypt/crypt_hash_descriptor.o src/libtomcrypt/misc/crypt/crypt_hash_is_valid.o src/libtomcrypt/misc/crypt/crypt_ltc_mp_descriptor.o src/libtomcrypt/misc/crypt/crypt_prng_descriptor.o src/libtomcrypt/misc/crypt/crypt_prng_is_valid.o src/libtomcrypt/misc/crypt/crypt_register_cipher.o src/libtomcrypt/misc/crypt/crypt_register_hash.o src/libtomcrypt/misc/crypt/crypt_register_prng.o src/libtomcrypt/misc/error_to_string.o src/libtomcrypt/misc/zeromem.o src/libtomcrypt/modes/ctr/ctr_decrypt.o src/libtomcrypt/modes/ctr/ctr_done.o src/libtomcrypt/modes/ctr/ctr_encrypt.o src/libtomcrypt/modes/ctr/ctr_setiv.o src/libtomcrypt/modes/ctr/ctr_start.o src/libtomcrypt/modes/ofb/ofb_decrypt.o src/libtomcrypt/modes/ofb/ofb_done.o src/libtomcrypt/modes/ofb/ofb_encrypt.o src/libtomcrypt/modes/ofb/ofb_getiv.o src/libtomcrypt/modes/ofb/ofb_setiv.o src/libtomcrypt/modes/ofb/ofb_start.o src/libtomcrypt/pk/asn1/der/bit/der_decode_bit_string.o src/libtomcrypt/pk/asn1/der/bit/der_encode_bit_string.o src/libtomcrypt/pk/asn1/der/bit/der_length_bit_string.o src/libtomcrypt/pk/asn1/der/integer/der_decode_integer.o src/libtomcrypt/pk/asn1/der/integer/der_encode_integer.o src/libtomcrypt/pk/asn1/der/integer/der_length_integer.o src/libtomcrypt/pk/asn1/der/object_identifier/der_decode_object_identifier.o src/libtomcrypt/pk/asn1/der/object_identifier/der_encode_object_identifier.o src/libtomcrypt/pk/asn1/der/object_identifier/der_length_object_identifier.o src/libtomcrypt/pk/asn1/der/octet/der_decode_octet_string.o src/libtomcrypt/pk/asn1/der/octet/der_encode_octet_string.o src/libtomcrypt/pk/asn1/der/octet/der_length_octet_string.o src/libtomcrypt/pk/asn1/der/sequence/der_decode_sequence_ex.o src/libtomcrypt/pk/asn1/der/sequence/der_decode_sequence_multi.o src/libtomcrypt/pk/asn1/der/sequence/der_encode_sequence_ex.o src/libtomcrypt/pk/asn1/der/sequence/der_encode_sequence_multi.o src/libtomcrypt/pk/asn1/der/sequence/der_length_sequence.o src/libtomcrypt/pk/asn1/der/sequence/der_sequence_free.o src/libtomcrypt/pk/asn1/der/short_integer/der_decode_short_integer.o src/libtomcrypt/pk/asn1/der/short_integer/der_encode_short_integer.o src/libtomcrypt/pk/asn1/der/short_integer/der_length_short_integer.o src/libtomcrypt/pk/asn1/der/utctime/der_encode_utctime.o src/libtomcrypt/pk/asn1/der/utctime/der_length_utctime.o src/libtomcrypt/pk/ecc/ecc.o src/libtomcrypt/pk/ecc/ecc_decrypt_key.o src/libtomcrypt/pk/ecc/ecc_encrypt_key.o src/libtomcrypt/pk/ecc/ecc_export.o src/libtomcrypt/pk/ecc/ecc_free.o src/libtomcrypt/pk/ecc/ecc_get_size.o src/libtomcrypt/pk/ecc/ecc_import.o src/libtomcrypt/pk/ecc/ecc_make_key.o src/libtomcrypt/pk/ecc/ecc_shared_secret.o src/libtomcrypt/pk/ecc/ecc_sign_hash.o src/libtomcrypt/pk/ecc/ecc_sizes.o src/libtomcrypt/pk/ecc/ecc_test.o src/libtomcrypt/pk/ecc/ecc_verify_hash.o src/libtomcrypt/pk/ecc/ltc_ecc_is_valid_idx.o src/libtomcrypt/pk/ecc/ltc_ecc_map.o src/libtomcrypt/pk/ecc/ltc_ecc_mulmod.o src/libtomcrypt/pk/ecc/ltc_ecc_mulmod_timing.o src/libtomcrypt/pk/ecc/ltc_ecc_points.o src/libtomcrypt/pk/ecc/ltc_ecc_projective_add_point.o src/libtomcrypt/pk/ecc/ltc_ecc_projective_dbl_point.o src/libtomcrypt/pk/rsa/rsa_decrypt_key.o src/libtomcrypt/pk/rsa/rsa_encrypt_key.o src/libtomcrypt/pk/rsa/rsa_exptmod.o src/libtomcrypt/pk/rsa/rsa_free.o src/libtomcrypt/pk/rsa/rsa_make_key.o src/libtomcrypt/pk/rsa/rsa_sign_hash.o src/libtomcrypt/pk/rsa/rsa_verify_hash.o src/libtomcrypt/prngs/fortuna.o src/libtomcrypt/prngs/rng_get_bytes.o src/libtomcrypt/prngs/rng_make_prng.o src/libtomcrypt/prngs/yarrow.o src/main.o src/minigmp/mini-gmp.o -larm_cortexM4l_math -lm 