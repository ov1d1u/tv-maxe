import os, subprocess, threading, urllib2, random, time, gobject

def which(program):
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

spauth = None
if which('sp-sc-auth'):
	spauth = 'sp-sc-auth'
elif which('sp-sc'):
	spauth = 'sp-sc'

class Protocol:
	def __init__(self, play_media, stop_media):
		self.play_media = play_media
		self.stop_media = stop_media
		self.params = {}
		self.progress = 0
		self.inport = None
		self.outport = None
		if not spauth:
			self.protocols = []
		else:
			self.protocols = ['sop://']

	def play(self, url, params = {}):
		self.progress = -1
		if not self.inport:
			self.port1 = random.randint(10025, 65535)
		else:
			self.port1 = self.inport
		if not self.outport :
			self.port2 = random.randint(10025, 65535)
		else:
			self.port2 = self.outport
		print "SopCast: Incoming port:", self.port1
		print "SopCast: Outgoing port:", self.port2
		try:
			os.kill(self.spc.pid, 9)
		except:
			pass
		self.spc = subprocess.Popen([spauth, url, str(self.port1), str(self.port2)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		threading.Thread(target=self.startmp, args=('http://127.0.0.1:' + str(self.port2),)).start()

	def startmp(self, url):
		playing = False
		if self.spc:
			self.progress = 0
			while (1):
				if not hasattr(self, 'spc'):
					break
				line = self.spc.stdout.readline()
				if 'nblockAvailable' in line:
					col = line.split()
					try:
						pr = col[2].split('=')
						try:
							percent = int(pr[1])
						except:
							percent = 0
						#if self.progress != -1:
							#self.progress = percent
						self.progress = percent
						if self.progress > 100:
							self.progress = -1
					except:
						pass
					if percent > 60:
						if not playing:
							gobject.idle_add(self.play_media, url)
							playing = True

				errorlevel = self.spc.poll()
				if errorlevel:
					if errorlevel != -9:
						gobject.idle_add(self.stop_media, "SopCast error.")
					return

	def stop(self):
		if hasattr(self, 'spc'):
			try:
				os.kill(self.spc.pid, 9)
			except:
				pass
		self.progress = -1

	def quit(self):
		if hasattr(self, 'spc'):
			try:
				os.kill(self.spc.pid, 9)
			except:
				pass
		self.progress = -1
