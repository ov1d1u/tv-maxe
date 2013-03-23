#-*- coding: utf-8 -*-
import urllib, urllib2, threading, time, datetime, gobject

class PBX:
	def __init__(self):
		self.working = False
		self.nrCanale = 0
		self.nrIncarcate = 0

	def signIn(self, username, password, callback):
		self.nrCanale = 0
		self.nrIncarcate = 0
		if self.working:
			return
		self.working = True
#		date_format = "%m/%d/%Y"
#		data = datetime.datetime.now()
#		atunci = datetime.datetime.strptime('12/8/2009', date_format)
#		acum  = datetime.datetime.strptime(str(data.month) + '/' + str(data.day) + '/' + str(data.year), date_format)
#		delta = acum - atunci
#		zile = delta.days
#		print zile
		pbxchannels = []
		url = 'http://romania.smcmobile.ro/list@' + username + '%5E' + password + '%5E1024%5E051'
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		data = response.read()
		if data.startswith('@'):
			self.working = False
			gobject.idle_add(callback, False)
			return
		gchannels = data.split('@')
		channels = gchannels[0]
		clist = channels.split(',')
		clist.pop(len(clist)-1)
		self.nrCanale = len(clist)-1
		
		date_format = "%m/%d/%Y"
		datac = datetime.datetime.now()
		atunci = datetime.datetime.strptime('12/8/' + str(datac.year-1), date_format)
		lastch = 'none'
		for x in clist:
			acum  = datetime.datetime.strptime(str(datac.month) + '/' + str(datac.day) + '/' + str(datac.year), date_format)
			delta = acum - atunci
			zile = delta.days
			chname = x
			lastch = lastch
			url = 'http://romania.smcmobile.ro/'+username+'%7C'+password+'%5E'+lastch+'%5E'+chname+'%5E1024%5E@Random%5E' + str(zile)
			try:
				req = urllib2.Request(url)
				response = urllib2.urlopen(req)
				data = response.read()
				if '://' in data:
					if data[0].isupper():
						churl = data[2:]
						pbxchannels.append([x, churl])
					else:
						churl = data
						pbxchannels.append([x, churl])
					lastch = x
			except:
				pass
				#lastch = x
			self.nrIncarcate = self.nrIncarcate + 1
			time.sleep(0.1)
		self.nrCanale = 0
		#self.working = False
		gobject.idle_add(callback, pbxchannels)
			
