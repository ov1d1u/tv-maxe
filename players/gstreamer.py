import gst, pygst, os, subprocess, threading, urllib2, random, time, gobject

class Player:
	def __init__(self, callback, xid):
		self.name = 'GStreamer'
		self.callback = callback
		self.xid = xid
		self.mprunning = False
		self.error = False
		self.imagesink = None
		self.player = None
		self.forceaspect = True
		self.tags = {}
		self.locks = 0			# de cate ori timpul a ramas acelasi
		self.lastPos = -1		# ultima pozitie (ultimul timp)
		# folosim ultimele doua variabile pentru a determina daca stream-ul s-a blocat
		
	def play(self, url):
		self.tags = {}
		self.locks = 0
		if url.startswith('/'):
			url = 'file://' + url
		self.url = url
		self.error = False
		threading.Thread(target=self.prepareGST, args=(url, )).start()
		
	def prepareGST(self, url):
		self.checked_video = False
		self.playing = False
		bin = gst.Bin('my-bin')
		self.textoverlay = gst.element_factory_make('textoverlay')
		bin.add(self.textoverlay)
		pad = self.textoverlay.get_pad("video_sink")
		ghostpad = gst.GhostPad("sink", pad)
		bin.add_pad(ghostpad)
		videosink = gst.gst_parse_bin_from_description("videobalance name=balance ! autovideosink", True)
		bin.add(videosink)
		gst.element_link_many(self.textoverlay, videosink)
		self.player = gst.element_factory_make("playbin2", "player")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("sync-message::element", self.on_sync_message)
		bus.connect("message", self.on_message)
		self.player.set_property("video-sink", bin)
		self.player.set_property("uri", url)
		self.player.set_state(gst.STATE_PLAYING)
		self.mprunning = True
		gobject.idle_add(self.callback)
		
	#def prepareGST(self, url):
		#self.checked_video = False
		#textsink = gst.element_factory_make('textoverlay', 'text')
		#videosink = gst.gst_parse_bin_from_description("videobalance name=balance ! autovideosink", True)
		#audiosink = gst.element_factory_make("autoaudiosink", "audiosink")
		#self.player.set_property("text-sink", textsink)
		#self.player.set_property("video-sink", videosink)
		#self.player.set_property("audio-sink", audiosink)
		#self.player.set_property("uri", url)
		#self.player.set_state(gst.STATE_PLAYING)
		#self.mprunning = True
		#gobject.idle_add(self.callback)
		
	def pause(self):
		if self.player:
			self.player.set_state(gst.STATE_PAUSED)
		
	def stop(self):
		if self.player:
			self.player.set_state(gst.STATE_NULL)
		self.mprunning = False
		self.imagesink = None
		
	def volume(self, value):
		if self.player:
			self.player.set_property("volume", value)
		
	def adjustImage(self, b, c, s):
		b = float(b) / float(100)
		c = float(c + 100) / float(100)
		s = float(s + 100) / float(100)
		try:
			if self.player:
				self.player.get_by_name("balance").set_property("brightness", b)
				self.player.get_by_name("balance").set_property("contrast", c)
				self.player.get_by_name("balance").set_property("saturation", s)
		except:
			pass
	
	def OSD(self, text):
		try:
			if hasattr(self, 'textoverlay'):
				self.textoverlay.set_property("halignment", 0)
				self.textoverlay.set_property("valignment", 2)
				self.textoverlay.set_property("line-alignment", 0)
				self.textoverlay.set_property("font-desc", "Sans Bold 18")
				self.textoverlay.set_property("text", text)
		except Exception, e:
			pass
		if hasattr(self, "timeout"):
			gobject.source_remove(self.timeout)
			self.timeout = gobject.timeout_add(5000, self.hideOSD)
		else:
			self.timeout = gobject.timeout_add(5000, self.hideOSD)
		
	def hideOSD(self):
		try:
			if hasattr(self, 'textoverlay'):
				self.textoverlay.set_property("text", "")
		except:
			pass
		return False
		
	def setRatio(self, ratio):
		if ratio == 0:
			self.forceaspect = True
		else:
			self.forceaspect = False
		if self.imagesink:
			self.imagesink.set_property("force-aspect-ratio", self.forceaspect)
		return None
	
	def getStatus(self):
		if self.mprunning:
			if self.player:
				try:
					time_format = gst.Format(gst.FORMAT_TIME)
					pos = self.player.query_position(time_format, None)[0]
					if pos == self.lastPos:
						self.locks = self.locks + 1 # adaugam un "lock"
					else:
						self.locks = 0
					self.lastPos = pos
					if self.locks > 40:
						print 'Error: Stream loading has taken too much'
						self.error = True	# prea mult timp cat stream-ul a ramas blocat; eroare.
					return not self.error
				except:
					return True
		else:
			return True
			
	def getTime(self):
		if self.mprunning:
			try:
				dur_int = self.player.query_duration(gst.FORMAT_TIME, None)[0]
				pos_int = self.player.query_position(gst.FORMAT_TIME, None)[0]
				return [divmod(pos_int, 1000000000)[0], divmod(dur_int, 1000000000)[0]]
			except:
				return [0, 0]
		else:
			return [0, 0]

	def getTags(self):
		artist = ''
		title = ''
		if self.tags.has_key('artist'):
			artist = self.tags['artist']
		if self.tags.has_key('title'):
			title = self.tags['title']
		return [artist, title]
			
	def changeAudio(self, id):
		id = int(id) - 1
		if self.player:
			self.player.set_property("current-audio", id)
	
	def isPlaying(self):
		return self.mprunning
		
	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == "prepare-xwindow-id":
			self.imagesink = message.src
			self.imagesink.set_xwindow_id(self.xid)
			self.imagesink.set_property("force-aspect-ratio", self.forceaspect)

	def on_message(self, bus, message):
		if message.type == gst.MESSAGE_TAG:
			tags = message.parse_tag()
			for tag_name in tags.keys():
  				if tag_name == 'organization':
  					self.tags['artist'] = tags[tag_name]
  				if tag_name == 'title':
  					self.tags['title'] = tags[tag_name]

	def quit(self):
		if self.player:
			self.player.set_state(gst.STATE_NULL)
		self.mprunning = False
