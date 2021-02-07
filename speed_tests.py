#!/usr/bin/env python3

import sys
import time
import statistics
import types
import argparse
import array


class test:
	def setup(self):
		pass
	def run(self):
		pass

def test_class(cls):
	cls._is_test = True
	return cls

# --- TESTS ---

# Containers

class l_index_get(test):
	def setup(self):
		self.cycles = 1_000_000
	def run(self):
		buff, buff2 = self.buff, 0
		for _ in range(self.cycles):
			buff2 = buff[_]

class l_index_set(test):
	def setup(self):
		self.cycles = 1_000_000
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff[_] = 0

@test_class
class list_index_get(l_index_get):
	'buff = list[_]'
	def setup(self):
		super().setup()
		self.buff = [1] * self.cycles

@test_class
class list_index_set(l_index_set):
	'list[_] = 0'
	def setup(self):
		super().setup()
		self.buff = [1] * self.cycles

@test_class
class array_index_get(l_index_get):
	'buff = array[_]'
	def setup(self):
		super().setup()
		self.buff = array.array('I', [1] * self.cycles)

@test_class
class array_index_set(l_index_set):
	'array[_] = 0'
	def setup(self):
		super().setup()
		self.buff = array.array('I', [1] * self.cycles)

@test_class
class memoryview_index_get(l_index_get):
	'buff = memoryview[_]'
	def setup(self):
		super().setup()
		self.buff = memoryview(array.array('I', [1] * self.cycles))

@test_class
class memoryview_index_set(l_index_set):
	'memoryview[_] = 0'
	def setup(self):
		super().setup()
		self.buff = memoryview(array.array('I', [1] * self.cycles))

@test_class
class tuple_index_get(l_index_get):
	'buff = tuple[_]'
	def setup(self):
		super().setup()
		self.buff = tuple(array.array('I', [1] * self.cycles))

@test_class
class dict_index_get(test):
	'buff = dict[_]'
	def setup(self):
		self.cycles = 1_000_000
		self.buff = {}
		for i in range(self.cycles):
			self.buff[i] = i
	def run(self):
		buff, buff2 = self.buff, 0
		for _ in range(self.cycles):
			buff2 = buff[_]

@test_class
class dict_index_set(test):
	'dict[_] = 0'
	def setup(self):
		self.cycles = 1_000_000
		self.buff = {}
		for i in range(self.cycles):
			self.buff[i] = i
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff[_] = 0

# String

class string(test):
	def setup(self):
		self.cycles = 100_000
		self.buff = ''

@test_class
class string_concatenate(string):
	'buff += " "'
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff += ' '

@test_class
class string_join(string):
	'buff.join(" ")'
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff = buff.join(' ')

@test_class
class string_format(string):
	'buff.format(...)'
	def run(self):
		buff, buff2 = '{0} {1} {2}', ''
		c1, c2 = 2, 3.0
		for _ in range(self.cycles // 10):
			buff2 = buff.format('1', c1, c2)

@test_class
class string_fstring(string):
	'f"{buff} ..."'
	def run(self):
		buff = ''
		c1, c2 = 2, 3.0
		for _ in range(self.cycles // 10):
			buff = f'{buff} {c1} {c2}'

@test_class
class string_cformat(string):
	'"%..." % (...)'
	def run(self):
		buff = ''
		c1, c2 = 2, 3.0
		for _ in range(self.cycles // 10):
			buff = '%s %i %f' % (buff, c1, c2)

# Class

@test_class
class class_attribute(test):
	'class.attribute = 0'
	class a:
		pass
	def setup(self):
		self.cycles = 1_000_000
		self.buff = self.a()
		self.buff._attribute = 0
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff._attribute = 0

@test_class
class class_slots_attribute(test):
	'class.attribute = 0 (with __slots__)'
	class a:
		__slots__ = ('_attribute',)
	def setup(self):
		self.cycles = 1_000_000
		self.buff = self.a()
		self.buff._attribute = 0
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff._attribute = 0

# Spetial cases

@test_class
class synthetic(test):
	'synthetic'
	class a:
		def __init__(self):
			self.data, self.data2 = 0, ''
		def inc(self):
			self.data += 1
			self.data2 += ' '
	def setup(self):
		self.cycles = 100_000
		self.buff = self.a()
	def run(self):
		buff = self.buff
		for _ in range(self.cycles):
			buff.inc()

# --- END TESTS ---

def parse_args():
	global log_level
	parser = argparse.ArgumentParser(description='Test the python interpreter speed')
	parser.add_argument('-a', '--all', action='store_true', help='run all tests')
	parser.add_argument('--csv', action='store_true', help='format results as csv (comma separated values). Do not use with -v option')
	parser.add_argument('-l', '--list', action='store_true', help='list availablere tests')
	parser.add_argument('-v', action='count', default=0, help='verbose level: -v, -vv')
	parser.add_argument('tests', metavar='[TEST1 [TEST2] ...]', nargs='*', help='space separated tests names. Use --list to list tests')
	ret = parser.parse_args()
	log_level = ret.v
	return ret

available_tests = { x:getattr(sys.modules[__name__], x) for x in dir()
	if isinstance(getattr(sys.modules[__name__], x), type) and issubclass(getattr(sys.modules[__name__], x), test) and  hasattr(getattr(sys.modules[__name__], x), '_is_test') }

args = parse_args()
if args.list:
	# list available tests
	available_tests_names_max_len = max(len(x) for x in available_tests)
	for i, kv in enumerate(available_tests.items()):
		name, func = kv
		print(f'{i+1:02} {name:{available_tests_names_max_len}} {func.__doc__ if func.__doc__ else name}')
else:
	print(f'{sys.version}')

	if args.all:
		# run all available tests
		tests_names = available_tests.keys()
	else:
		# check for allowable tests
		tests_names, wrong_names = [], []
		for _ in args.tests:
			if _.isdigit():
				if int(_) > 0 and int(_) <= len(available_tests):
					tests_names.append(tuple(available_tests.keys())[int(_) - 1])
				else:
					wrong_names.append(_)
			elif _ not in available_tests:
				wrong_names.append(_)
			else:
				tests_names.append(_)
		if wrong_names:
			print(f'Unknown tests: {", ".join(wrong_names)}')
			print('Use --list to list tests')
			sys.exit(1)

	# run tests
	def run_test(test_class, tests_count=7):
		'runs one test for several times'
		print(f'{test_class.__name__:{tests_names_max_len}}{delimiter}', end='\n' if log_level > 0 else '', flush=True)
		time_results = [] # tests time measurements
		for _ in range(tests_count):
			if log_level > 0:
				print(f'\ttest: {_+1}')
			# prepare the test
			tc = test_class()
			tc.setup()
			# run the test with time measurement
			t = time.process_time()
			tc.run()
			elapsed_time = time.process_time() - t
			time_results.append(elapsed_time)
		# tests done # process the time measurements
		if args.csv:
			print(f'{statistics.mean(time_results):1.3}{delimiter}{min(time_results):1.3}{delimiter}{max(time_results):1.3}'
				f'{delimiter}{((max(time_results)-min(time_results))/max(time_results))*100:1.3}%')
		else:
			print(f'avg={statistics.mean(time_results):1.3}{delimiter}min={min(time_results):1.3}{delimiter}max={max(time_results):1.3}'
				f'{delimiter}delta={((max(time_results)-min(time_results))/max(time_results))*100:1.3}% ({max(time_results)-min(time_results):1.3})')

	tests_names_max_len = max(len(x) for x in tests_names)
	delimiter = ',' if args.csv else ' '
	if args.csv:
		print(f'name{delimiter}avg{delimiter}min{delimiter}max{delimiter}delta')
	for _ in tests_names:
		run_test(available_tests[_])
