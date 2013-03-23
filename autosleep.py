import gtk, gobject, os

class Sleep:
	def __init__(self, main):
		self.gui = main.gui
		self.quit = main.quit
		self.OSD = main.OSD
		self.timer = None
		self.warning_timer = None
		self.endtime = 0
		self.remoteiter = -1			# for IR remote
		self.remoteres = None			# for IR, we want to initially show remaining time on first press in a while
		self.shutdown_cmd = main.settingsManager.getShutdown()
	
	def show(self, obj, event=None):
		self.gui.get_object('shutdown_check').set_sensitive(True)
		if self.timer:
			diff = (self.endtime - int(gobject.get_current_time())) / 60
			self.gui.get_object('spinbutton4').set_value(int(diff))
			self.gui.get_object('lblShutdownCancel').show()
		else:
			self.gui.get_object('spinbutton4').set_value(0)
		self.gui.get_object('sleepw').show()
		
	def hide(self, obj, event=None):
		self.gui.get_object('sleepw').hide()
		return True

	def ok(self, obj, event=None):
		self.set_shutdown(int(self.gui.get_object('spinbutton4').get_value()), self.gui.get_object('shutdown_check').get_active())
		self.remoteiter = -1
		self.hide(None)
		
	def set_shutdown(self, value, halt=False):
		if self.timer:
			gobject.source_remove(self.timer)
			if self.warning_timer:
				gobject.source_remove(self.warning_timer)
				self.warning_timer = None
			self.timer = None
		timeout = value * 1000 * 60
		if timeout == 0:
			self.cancel(None)
		else:
			if value > 1:
				self.warning_timer = gobject.timeout_add((value * 1000 * 60) - 60000, self.warning)
			self.timer = gobject.timeout_add(timeout, self.shutdown, halt)
			self.endtime = int(gobject.get_current_time()) + timeout / 1000
			
	def cancel(self, obj, event=None):				# cancel shutdown, not cancel button
		if self.timer:
			gobject.source_remove(self.timer)
			if self.warning_timer:
				gobject.source_remove(self.warning_timer)
				self.warning_timer = None
			self.timer = None
			self.endtime = None
			self.gui.get_object('lblShutdownCancel').hide()
			self.gui.get_object('spinbutton4').set_value(0)
		return True
		
	def shutdown(self, halt=False):
		if halt:
			try:
				os.system(self.shutdown_cmd)
			except:
				print 'ERROR: Cannot shutdown system'
		self.quit()

	def remote(self):
		cycles = [0, 15, 30, 60, 120, 180]
		next = 0
		if self.timer:
			diff = (self.endtime - int(gobject.get_current_time())) / 60
			if self.remoteiter == -1:
				self.OSD("Sleep: " + str(diff) + ' min')
				if diff > cycles[len(cycles)-1]:
					self.remoteiter = 0
				else:
					for c, t in enumerate(cycles):
						if diff >= t:
							self.remoteiter = c
			else:
				if self.remoteiter > len(cycles)-1:
					self.remoteiter = 0
				next = cycles[self.remoteiter]
				if next > 0:
					self.OSD("Sleep: " + str(next) + " min\nWarning: this will turn off your computer!")
					self.set_shutdown(next, True)
				else:
					self.cancel(None)
					self.OSD("Sleep: disabled")
		else:
			if self.remoteiter == -1:
				self.OSD("Sleep: disabled")
				self.cancel(None)
				self.remoteiter = 0
			else:
				if self.remoteiter > len(cycles)-1:
					self.remoteiter = 0
				next = cycles[self.remoteiter]
				if next > 0:
					self.OSD("Sleep: " + str(next) + " min\nWarning: this will turn off your computer!")
					self.set_shutdown(next, True)
				else:
					self.cancel(None)
					self.OSD("Sleep: disabled")
		self.remoteiter = self.remoteiter + 1
		if self.remoteres:
			gobject.source_remove(self.remoteres)
		self.remoteres = gobject.timeout_add(3000, self.reset_remote)

	def warning(self):
		self.OSD("Sleep: 1 minute left")
		return False
		
	def reset_remote(self):
		self.remoteiter = -1
		return False
		
	def get_minutes_left(self):
		if self.timer:
			return (self.endtime - int(gobject.get_current_time())) / 60
		else:
			return 0
