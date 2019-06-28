#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Atmel Studio Project file Converter

from __future__ import print_function
import sys
import datetime
import os
from lxml import etree
import argparse


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
			self.linker_libraries, self.linker_library_search_paths, self.linker_other_flags = [], [], ''

	def __init__(self, project_file_path):

		def get_subelement_text(parent_element, subelement_name):
			subelement = parent_element.xpath('x:{}'.format(subelement_name), namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003})
			return AtmelStudioCProjectFile.unescape(subelement[0].text) if subelement else ''

		def get_subelements_list_texts(parent_element, subelement_name):
			subelement_list = parent_element.xpath('x:{}/x:ListValues/*'.format(subelement_name), namespaces={'x': AtmelStudioCProjectFile.NAMESPACE_MSBUILD_2003})
			return [ AtmelStudioCProjectFile.unescape(i.text) for i in subelement_list ] if subelement_list else []

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
						condition.linker_other_flags = ' '.join(get_subelements_list_texts(arm_gcc, 'armgcc.linker.miscellaneous.OtherOptions'))
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
			return 'condition: "{}"; defines: "{}"; compiler_optimization: "{}"; compiler_other_flags: "{}"; compiler_debug_level: "{}"; linker_libraries: "{}"; linker_library_search_paths: "{}"; linker_other_flags: "{}"; include_paths: "{}"'.format(
				condition.condition, '", "'.join(condition.defines), condition.compiler_optimization, condition.compiler_other_flags, condition.compiler_debug_level, '", "'.join(condition.linker_libraries), '", "'.join(condition.linker_library_search_paths), condition.linker_other_flags, '", "'.join(condition.include_paths))
		ret = 'Project: "{}"; device: "{}"; files: "{}"; exclude_files: "{}"'.format(
				self.name, self.device, '", "'.join(self.files), '", "'.join(self.exclude_files))
		for condition in self.conditions:
			ret += '; '+condition_str(condition)
		return ret


def write_eclipse_cdt_includes_and_symbols_xml(cproject, condition, includes_and_symbols_xml_path):

	def write_section(name, languages, texts):
		xml_file.write(('\t<section name="{}">\n').format(name))
		for i in languages:
			xml_file.write(('\t\t<language name="{}">\n').format(i))
			for ii in texts:
				xml_file.write(('\t\t\t{}\n').format(ii))
			xml_file.write('\t\t</language>\n')
		xml_file.write('\t</section>\n')

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

	def remove_prefix(text, prefix):
		if prefix and text.startswith(prefix):
			text = text[len(prefix):]
		return text


	with open(includes_and_symbols_xml_path, 'w') as xml_file:
		xml_file.write(('<?xml version="1.0" encoding="UTF-8"?>\n<!-- {} This is auto-generated file from Atmel Studio project "{}", device "{}", condition "{}" -->\n').format(datetime.datetime.now().isoformat(), cproject.name, cproject.device, condition.condition))
		xml_file.write('<cdtprojectproperties>\n')
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
		xml_file.write('</cdtprojectproperties>\n')

if __name__ == "__main__":

	def escape_path(path):
		return "".join(x for x in path if (x.isalnum() or x in "._-()[]{}+-'= "))

	parser = argparse.ArgumentParser(description='Project conversion: Eclipse <-> Atmel studio')
	parser.add_argument('PROJECT_FILE', help='project file path')
	# parser.add_argument('--htm', action='store_true', help='sum the integers (default: find the max)')	
	parser.add_argument('--include-path-remove-prefix', metavar='PREFIX_TO_REMOVE', help='remove prefix from include paths')	
	args = parser.parse_args()

	cproject = AtmelStudioCProjectFile(args.PROJECT_FILE)

	# print the html
	print('<html>\n\t<body>')
	# project info
	print(('\t\t<h1>Atmel Studio project file converter</h1>\n\t\t<table frame="border" cellpadding="5"><tr><td>Date &amp; time</td><td>{}</td></tr>\n\t\t<tr><td>Name</td><td>{}</td></tr>\n\t\t<tr><td>Device</td><td>{}</td></tr></table>').format(datetime.datetime.now().isoformat(), cproject.name, cproject.device))
	# content table
	print('<hr/><h2>Table of contents</h2>')
	for condition_index, condition in zip(xrange(len(cproject.conditions)), cproject.conditions):
		print('<p><a href="#'+str(condition_index+1)+'">'+str(condition_index+1)+'. '+condition.condition+'</a></p>')
	print('<p><a href="#'+str(len(cproject.conditions)+1)+'">'+str(len(cproject.conditions)+1)+'. Files</a></p>')
	print('<p><a href="#'+str(len(cproject.conditions)+2)+'">'+str(len(cproject.conditions)+2)+'. Exclude files</a></p>')
	# conditions
	for condition_index, condition in zip(xrange(len(cproject.conditions)), cproject.conditions):
		print('<hr/><h2 id="'+str(condition_index+1)+'">'+str(condition_index+1)+'. '+condition.condition+'</h2>')
		# defines
		print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.1. Defines</h3></caption>')
		for i, f in zip(xrange(len(condition.defines)), sorted(condition.defines)):
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
		for i, f in zip(xrange(len(condition.linker_libraries)), sorted(condition.linker_libraries)):
			print('<tr><td>'+('Libraries' if i==0 else '')+'</td><td>'+f+'</td></tr>')
		for i, f in zip(xrange(len(condition.linker_library_search_paths)), sorted(condition.linker_library_search_paths)):
			print('<tr><td>'+('Library search path' if i==0 else '')+'</td><td>'+f+'</td></tr>')
		print('<tr><td>Other flags</td><td>'+condition.linker_other_flags+'</td></tr>')
		print('</table>')
		# include paths
		print('<table frame="border" cellpadding="5"><caption><h3 style="text-align:left">'+str(condition_index+1)+'.5. Include paths</h3></caption>')
		for i, f in zip(xrange(len(condition.include_paths)), sorted(condition.include_paths)):
			print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
		print('</table>')
	# files
	print('<hr/><table frame="border" cellpadding="5"><caption><h2 id="'+str(len(cproject.conditions)+1)+'" style="text-align:left">'+str(len(cproject.conditions)+1)+'. Files</h2></caption>')
	for i, f in zip(xrange(len(cproject.files)), sorted(cproject.files)):
		print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
	print('</table>')
	# exclude files
	print('<hr/><table frame="border" cellpadding="5"><caption><h2 id="'+str(len(cproject.conditions)+2)+'" style="text-align:left">'+str(len(cproject.conditions)+2)+'. Exclude files</h2></caption>')
	for i, f in zip(xrange(len(cproject.exclude_files)), sorted(cproject.exclude_files)):
		print('<tr><td>'+str(i+1)+'</td><td>'+f+'</td></tr>')
	print('</table>')
	print('\t</body>\n</html>')
	# print(str(cproject))

	for condition in cproject.conditions:
		write_eclipse_cdt_includes_and_symbols_xml(cproject, condition, os.path.join(os.path.dirname(args.PROJECT_FILE), 'eclipse settings '+escape_path(condition.condition)+'.xml'))

	with open(os.path.join(os.path.dirname(args.PROJECT_FILE), 'eclipse cproject.xml'), 'w') as xml_file:
		xml_file.write('<sourceEntries>\n\t<entry excluding="'+'|'.join(cproject.exclude_files)+'" flags="VALUE_WORKSPACE_PATH" kind="sourcePath" name=""/>\n</sourceEntries>')
