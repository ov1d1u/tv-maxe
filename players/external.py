import os, subprocess

class Player:
	def __init__(self, callback, exe):
		self.name = 'External'
		self.callback = callback
		self.exe = exe
		self.player = None
		self.error = False
		self.mprunning = False
		self.mp = None
		
	def play(self, url):
		self.player = subprocess.Popen([self.exe, url])
		self.mprunning = True
		self.callback()
		
	def pause(self):
		print 'Not supported in external player mode'
		return
			
	def stop(self):
		self.mprunning = False
		if self.player:
			self.player.terminate()
			self.player = None
	
	def volume(self, value):
		print 'Not supported in external player mode'
		return
			
	def adjustImage(self, b, c, s):
		print 'Not supported in external player mode'
		return

	def OSD(self, text):
		print 'Not supported in external player mode'
		return
	
	def setRatio(self, ratio):
		print 'Not supported in external player mode'
		return
			
	def getStatus(self):
		return not self.error
			
	def getTime(self):
		return [0, 0]
		
	def getTags(self):
		return ['', '']
	
	def seek(self, t):
		print 'Not supported in external player mode'
		return
	
	def isPlaying(self):
		return self.mprunning
	
	def quit(self):
		self.mprunning = False
		if self.player:
			self.player.terminate()
			self.player = None
		 
