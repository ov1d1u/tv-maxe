key = 127

class KeySim:
	def __init__(self):
		self.src = 0
		try:
			import virtkey
			self.v = virtkey.virtkey()
		except:
			print 'virtkey module not available'
		
	def start(self):
		if hasattr(self, 'v'):
			self.v.press_keycode(key)
			self.v.release_keycode(key)
			self.v.release_keycode(key)
			return True
		else:
			return False
