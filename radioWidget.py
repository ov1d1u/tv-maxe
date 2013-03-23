import gtk, gobject, threading, time

class RadioWidget:
	def __init__(self, outer):
		self.gui = outer.gui
		self.tvmaxe = outer
		self.currentIter = None
		self.channels = outer.channels
		
	def modRadio(self, obj):
		self.tvmaxe.radioMode = True
		self.gui.get_object('notebook2').set_current_page(1)
		self.gui.get_object('window1').hide()
		self.gui.get_object('window13').show()
		self.gui.get_object('menuitem39').hide()
		threading.Thread(target=self.readTags).start()
				
	def modTV(self, obj, event=None):
		self.tvmaxe.radioMode = False
		self.gui.get_object('window1').show()
		self.gui.get_object('window13').hide()
		self.gui.get_object('menuitem39').show()
		return True
	
	def updateWidget(self, name, url, logo):
		self.gui.get_object('label81').set_label(name)
		self.gui.get_object('label82').set_label(url)
		self.gui.get_object('image25').set_from_pixbuf(logo)
	
	def play(self, obj, t):
		self.tvmaxe.playRadioChannel(t)
	
	def readTags(self):
		while self.gui.get_object('window13').get_visible():
			if self.tvmaxe.mediaPlayer.isPlaying():
				tags = self.tvmaxe.mediaPlayer.getTags()
				gobject.idle_add(self.setTitle, tags)
			time.sleep(5)
			
	def setTitle(self, tags):
		self.gui.get_object('label81').set_tooltip_text('')
		self.gui.get_object('label82').set_tooltip_text('')
		if len(tags[0]) > 1:
			self.gui.get_object('label81').set_label(tags[0])
			self.gui.get_object('label81').set_tooltip_text(tags[0])
		if len(tags[1]) > 1:
			self.gui.get_object('label82').set_label(tags[1])
			self.gui.get_object('label82').set_tooltip_text(tags[1])
