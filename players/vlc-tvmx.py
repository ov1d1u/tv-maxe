import vlc, os, subprocess, threading, urllib2, random, time, gobject

class Player:
	def __init__(self, callback, xid):
		self.name = 'VLC-tvmx'
		self.callback = callback
		self.xid = xid
		self.mprunning = False

	def play(self, url):
		Instance = vlc.Instance()
		self.mp = vlc.MediaPlayer(Instance)
		self.mp.set_xwindow(self.xid)
		self.mp.video_set_mouse_input(False)
		self.mp.video_set_key_input(False)
		self.mp.set_mrl(url)
		self.error = False
		self.mp.play()
		self.mprunning = True
		threading.Thread(target=self.startmp).start()
		
	def startmp(self):
		while self.mp.get_state() == vlc.State.Opening:
			time.sleep(0.1)
		if self.mp.get_state() == vlc.State.Error:
			self.error = True
		gobject.idle_add(self.callback)
		
	def pause(self):
		if hasattr(self, 'mp'):
			self.mp.pause()
	
	def stop(self):
		if hasattr(self, 'mp'):
			self.mp.stop()
			self.mprunning = False
			
	def volume(self, value):
		if hasattr(self, 'mp'):
			self.mp.audio_set_volume(int(value*100))
		
	def adjustImage(self, b, c, s):
		if hasattr(self, 'mp'):
			try:
				b = (float(b) + float(100)) / float(100)
				c = (float(c) + float(100)) / float(100)
				s = (float(s) + float(100)) / float(100)
				self.mp.video_set_adjust_int(vlc.VideoAdjustOption.Enable, True)
				self.mp.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, b)
				self.mp.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, c)
				self.mp.video_set_adjust_float(vlc.VideoAdjustOption.Saturation, s)
			except:
				pass
	
	def OSD(self, text):
		if hasattr(self, 'mp'):
			try:
				self.mp.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, True)
				self.mp.video_set_marquee_string(vlc.VideoMarqueeOption.Text, text)
				self.mp.video_set_marquee_int(vlc.VideoMarqueeOption.Timeout, 4000)
			except:
				pass
		
	def setRatio(self, ratio):
		if ratio == 0:
			ratio = None
		elif ratio == 1:
			ratio = '1:1'
		elif ratio == 2:
			ratio = '3:2'
		elif ratio == 3:
			ratio = '4:3'
		elif ratio == 4:
			ratio = '5:4'
		elif ratio == 5:
			ratio = '14:9'
		elif ratio == 6:
			ratio = '14:10'
		elif ratio == 7:
			ratio = '16:9'
		elif ratio == 8:
			ratio = '16:10'
		elif ratio == 9:
			ratio = '2.35:1'
		if hasattr(self, 'mp'):
			self.mp.video_set_aspect_ratio(ratio)
	
	def getStatus(self):
		if hasattr(self, 'mp'):
			state = self.mp.get_state()
			if state == vlc.State.Error:
				self.mp.stop()
				return False
			return True
		else:
			return False
			
	def getTime(self):
		if hasattr(self, 'mp'):
			try:
				return [self.mp.get_time() / 1000, self.mp.get_length() / 1000]
			except:
				return [0, 0]
		else:
			return [0, 0]

	def getTags(self):
		tags = ['', '']
		media = self.mp.get_media()
		title = media.get_meta(vlc.Meta.NowPlaying)
		artist = media.get_meta(vlc.Meta.Title)
		if artist:
			tags[0] = artist
		if title:
			tags[1] = title
		return tags

	def isPlaying(self):
		return self.mprunning
	
	def changeAudio(self, id):
		self.mp.audio_set_track(int(id))
	
	def quit(self):
		self.mprunning = False
		try:
			if hasattr(self, 'mp'):
				self.mp.stop()
		except:
			pass
