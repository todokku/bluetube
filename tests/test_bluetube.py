#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import unittest
from bluetube import Bluetube
from bluetube import Feeds
from mock import patch


class TestBluetube(unittest.TestCase):
	'''The main tester class'''

	class InFeed(object):
		def __init__(self, author, title):
			self.title = title
			self.author = author
	
	
	class FakeFeed(object):
		def __init__(self, author, title, entries=[]):
			self.feed = TestBluetube.InFeed(title, author)
			self.entries = entries
			

	@staticmethod
	def good_side_effect(*args, **kwargs):
		if '--version' in args[0]:
			pass
		elif 'youtube-dl' in args[0][0]:
			assert os.path.exists(kwargs['cwd']) and os.path.isdir(kwargs['cwd']), \
				'{} directory is not found'.format(kwargs['cwd'])
			name = args[0][-1].split('=')[1]
			ext = None
			for x in args[0]:
				if '--audio-format' in x:
					ext = x.split()[-1]
					break
			assert ext, 'no --audio-format found in the command'
			with open(os.path.join(kwargs['cwd'], '{}.{}'.format(name, ext)), 'w') as f:
				f.write(str(args))
		elif 'blue' in args[0][0]:
			path = os.path.join(kwargs['cwd'], args[0][-1])
			assert os.path.exists(path) and os.path.isfile(path), \
				'{} not found'.format(path)
		return 0
		
	def setUp(self):
		self.SUT = Bluetube()

	def tearDown(self):
		if os.path.isfile(Feeds.DATABASE_FILE) and os.path.exists(Feeds.DATABASE_FILE):
			os.remove(Feeds.DATABASE_FILE)
		if os.path.isfile(Bluetube.CONFIG_FILE) and os.path.exists(Bluetube.CONFIG_FILE):
			os.remove(Bluetube.CONFIG_FILE)

	@patch('bluetube.feedparser.parse')
	def test_add_list_remove(self, mocked_feed):
		mocked_feed.side_effect = [TestBluetube.FakeFeed(u"Евгений Вольнов", u"Настенька"),
								TestBluetube.FakeFeed(u"Евгений Вольнов", u"Настенька"),
								TestBluetube.FakeFeed(u"Вольнов Talks", u"Все відео"),
								TestBluetube.FakeFeed(u"ВатаШоу", u"Чатрулетка")
		]

		url1 = 'https://www.youtube.com/watch?v=4bvAIa5hjFk&list=PLV4xApIh67zHZXf4DoSDtXqVvneSgh-1X'
		url2 = 'https://www.youtube.com/watch?v=GKJLAvTrRKA&list=PLlnMlUDFFfEs8eO4L3haB5V1qO2syoHQJ'
		url3 = 'https://www.youtube.com/watch?v=2y3gqxklW04&list=PLU8zrvU8pCeXhM_32znSFmCBFuswP5_Cv'

		print('ADDING CHANNELS')
		ret = self.SUT.add_channel(url1, 'a')
		self.assertFalse(ret, 'add channel 1 failed')

		ret = self.SUT.add_channel(url1, 'a')
		self.assertFalse(ret, 'add channel 1 for the second time failed')

		ret = self.SUT.add_channel(url2, 'v')
		self.assertFalse(ret, 'add channel 2 failed')

		ret = self.SUT.add_channel(url3, 'v')
		self.assertFalse(ret, 'add channel 3 failed')

		print('SHOW ALL CHANNELS')
		self.SUT.list_channels()
# 
		print('REMOVE ONE CHANNAL THAT DOES EXIST')
		self.SUT.remove_channel(u'Вольнов Talks', u'Все видео канала')
		

		print('REMOVE A NON-EXISTAING CHANNAL')
		self.SUT.remove_channel(u'author', u'name')

		print('REMOVE ANOTHER CHANNAL THAT DOES EXIST')
		self.SUT.remove_channel(u'Евгений Вольнов', u'Настенька')

		print('SHOW ALL CHANNELS AGAIN')
		self.SUT.list_channels()

	@patch('bluetube.subprocess.call')
	def test_run_precondition_fails(self, mocked_call):
		'''1st - no configs
		   2nd - no youtube-dl 
		   3rd - no blutooth-send'''
		
		self.assertTrue(self.SUT.run(), 'No configuration file, the case should fail')
		
		self._create_a_configuration_file()
		
		mocked_call.side_effect = [OSError(-1, 'no youtube-dl'),
								OSError(0, ''),
								OSError(-1, 'no bluetooth-send')]
		self.assertTrue(self.SUT.run(), 'No youtube-dl in the PATH, the case should fail')
		self.assertTrue(self.SUT.run(), 'No bluetooth-send in the PATH, the case should fail')
		print('DONE')


	@patch('bluetube.raw_input')
	@patch('bluetube.feedparser.parse')
	@patch('bluetube.subprocess.call')
	def test_run(self, mocked_call, mocked_feed_parse, mocked_raw_input):

		mocked_call.side_effect = TestBluetube.good_side_effect

		entries = [{'title': u'Маркевич — як помирали Металіст та Дніпро',
					'link' : 'https://www.youtube.com/watch?v=1'},
					{'title': u'Сабо - як відривалися радянські футболісти та про Динамо за лаштунками',
					'link': 'https://www.youtube.com/watch?v=2'}
				]
		mocked_feed_parse.side_effect = [TestBluetube.FakeFeed(u"Вацко Live", u"Вацко Light"),
										TestBluetube.FakeFeed(u"Вацко Live", u"Вацко Light", entries)]
		mocked_raw_input.side_effect = ['y', 'n']
		self._create_a_configuration_file()

		print('ADDING CHANNELS')
		# use real URL in order to pass the validation
		ret = self.SUT.add_channel('https://www.youtube.com/watch?v=VTC8gj01s6g&list=PL17KOAV8JBN_uE7v4qgQxLX7kno4G9HyQ', 'a')
		self.assertFalse(ret, 'add channel failed')
		
		ret = self.SUT.run()
		self.assertFalse(ret, 'run failed')
	
	def _create_a_configuration_file(self):
		with open(Bluetube.CONFIG_FILE, 'w') as f:
			f.write(Bluetube.DEFAULT_CONFIGS)


if __name__ == "__main__":
	unittest.main()
