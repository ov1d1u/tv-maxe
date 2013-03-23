#-*- coding: utf-8 -*-
import threading, time, urllib2

class ListParser:
	def __init__(self):
		self.itm = False
	
	def getData(self, url):
		self.url = url
		if self.url.endswith('.pls'):
			self.getPLSitem()
		elif self.url.endswith('.m3u'):
			self.getM3Uitem()
		
		while not self.itm:
			time.sleep(0.1)
		return self.itm
			
	def getPLSitem(self):
		self.itm = False
		req = urllib2.Request(self.url)
		response = urllib2.urlopen(req)
		data = response.read()
		for x in data.split("\n"):
			if x.startswith("File1="):
				self.itm = x[6:]
				break
			
	def getM3Uitem(self):
		self.itm = False
		req = urllib2.Request(self.url)
		response = urllib2.urlopen(req)
		data = response.read()
		for x in data.split("\n"):
			if not x.startswith("#"):
				self.itm = x
				break
	
		
