import mpylayer
import os, subprocess, threading, urllib2, random, time, gobject

class Player:
	def __init__(self, callback, xid):
		self.name = 'MPlayer'
		self.xid = xid
		self.callback = callback
		self.error = False
		self.mprunning = False
		self.mp = None
		
	def play(self, url):
		if not self.mp:
			self.mp = mpylayer.MPlayerControl(extra_args=['-wid', str(self.xid), '-vf', 'eq2', '-sub-bg-alpha', '25', '-subfont-osd-scale', '2', '-fixed-vo', '-af', 'volume', '-volume', '0', '-cache', '256'])
		self.mprunning = False
		self.error = False
		threading.Thread(target=self.startmp, args=(url,)).start()
		
	def startmp(self, url):
		self.contrast = 0
		self.brightness = 0
		self.saturation = 0
		self.mprunning = True
		self.mp.loadfile(url)
		timp = int(time.time())
		while self.mp.time_pos == None:
			if (int(time.time()) - timp > 45):
				self.error = True
				break
			if not self.mprunning:
				return
			time.sleep(0.1)
		gobject.idle_add(self.callback)
		
	def pause(self):
		if self.mp:
			self.mp.pause()
			
	def stop(self):
		if self.mp:
			self.mprunning = False
			try:
				self.mp.stop()
				self.mp.quit()
			except:
				pass
	
	def volume(self, value):
		if not self.mp:
			return
		v = value * 100
		if v > 100.0:
			v = 100.0
		else:
			self.mp.volume = v
			
	def adjustImage(self, b, c, s):
		if not self.mp:
			return
		try:
			if int(b) != self.brightness:
				self.mp.run_command('brightness', str((int(b)-self.brightness)))
				self.brightness = int(b)
			if int(s) != self.saturation:
				self.mp.run_command('saturation', str((int(s)-self.saturation)))
				self.saturation = int(s)
			if int(c) != self.contrast:
				self.mp.run_command('contrast', str((int(c)-self.contrast)))
				self.contrast = int(c)
		except:
			pass

	def OSD(self, text):
		if not self.mp:
			return
		if text:
			text = text.replace('\n', ' :: ')
			self.mp.osd_show_text(text, 4000)
	
	def setRatio(self, ratio):
		if not self.mp:
			return
		if ratio == 0:
			ratio = 0
		elif ratio == 1:
			ratio = 1
		elif ratio == 2:
			ratio = 1.5
		elif ratio == 3:
			ratio = 1.33
		elif ratio == 4:
			ratio = 1.25
		elif ratio == 5:
			ratio = 1.55
		elif ratio == 64:
			ratio = 1.4
		elif ratio == 7:
			ratio = 1.77
		elif ratio == 8:
			ratio = 1.6
		elif ratio == 9:
			ratio = 2.35

		self.mp.switch_ratio(ratio)
			
	def getStatus(self):
		return not self.error
			
	def getTime(self):
		if not self.mp:
			return [0, 0]
		try:
			total = int(float(self.mp.time_length))
			now = int(float(self.mp.time_pos))
			return [now, total]
		except Exception, e:
			return [0, 0]

	def getTags(self):
		try:
			return [self.mp.radiometa[0], self.mp.radiometa[1]]
		except:
			return ['', '']
	
	def seek(self, t):
		if not self.mp:
			return
		try:
			self.mp.seek(int(t/1000), 2)
		except:
			print 'seek failed'
			
	def changeAudio(self, id):
		self.mp.run_command('switch_audio', float(id))
	
	def isPlaying(self):
		return self.mprunning
	
	def quit(self):
		self.mprunning = False
		try:
			if self.mp:
				self.mp.quit()
		except:
			pass
		
