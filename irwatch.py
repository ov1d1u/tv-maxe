import os, subprocess, threading, gobject
#-*- coding: utf-8 -*-

class IRwatch:
	def __init__(self):
		try:
			self.irw = subprocess.Popen(['irw'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		except:
			self.irw = None
		self.callbacks = []#{}
		
	def listen(self):
		if self.irw:
			while self.irw:
				try:
					line = self.irw.stdout.readline()
					cols = line.split()
					keycode = cols[0]
					for x in self.callbacks:
						if type(x) == list:
							cb = x[0]
							params = x[1]
							cb(keycode, *params)
						else:
							x(keycode)
				except Exception, e:
					pass
				
				if self.irw.poll():
					return
			
	def quit(self):
		try:
			self.irw.terminate()
		except:
			pass
		
class Main:
	def __init__(self, cb_dict):
		self.infrared = IRwatch()
		self.cb_dict = cb_dict
		self.quit = self.infrared.quit
		self.settingsManager = None

	def initRemote(self, settingsManager):
		self.settingsManager = settingsManager
		self.infrared.callbacks.append(self.receiveIR)
		threading.Thread(target=self.infrared.listen).start()
	
	def receiveIR(self, code):
		if self.settingsManager:
			if code == self.settingsManager.remote_playpause:
				gobject.idle_add(self.cb_dict['playpause'], None)
			if code == self.settingsManager.remote_switch_fullscreen:
				gobject.idle_add(self.cb_dict['fullscreen'], None)
			if code == self.settingsManager.remote_stop:
				gobject.idle_add(self.cb_dict['stop'], None)
			if code == self.settingsManager.remote_volumeup:
				gobject.idle_add(self.cb_dict['setVolume'], None, None, 0.1)
			if code == self.settingsManager.remote_volumedown:
				gobject.idle_add(self.cb_dict['setVolume'], None, None, -0.1)
			if code == self.settingsManager.remote_mute:
				gobject.idle_add(self.cb_dict['mute'])
			if code == self.settingsManager.remote_quit:
				gobject.idle_add(self.cb_dict['quit'], None)
			if code == self.settingsManager.remote_nextchannel:
				gobject.idle_add(self.cb_dict['nextChannel'])
			if code == self.settingsManager.remote_prevchannel:
				gobject.idle_add(self.cb_dict['prevChannel'])
			if code == self.settingsManager.remote_info:
				gobject.idle_add(self.cb_dict['showEPG'])
			if code == self.settingsManager.remote_up:
				gobject.idle_add(self.cb_dict['remoteUP'])
			if code == self.settingsManager.remote_down:
				gobject.idle_add(self.cb_dict['remoteDOWN'])
			if code == self.settingsManager.remote_ok:
				gobject.idle_add(self.cb_dict['remoteOK'])
			if code == self.settingsManager.remote_sleep:
				gobject.idle_add(self.cb_dict['remoteSLEEP'])
		
	def stopRemote(self):
		try:
			self.infrared.callbacks.pop(self.infrared.callbacks.index(self.receiveIR))
		except:
			pass
		self.infrared.quit()
