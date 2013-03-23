import sys, os, subprocess, time, datetime, pickle, socket
from daemon import Daemon

#workaround to import channel
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parentdir) 

class TVMaxe_d(Daemon):
	def __init__(self, tvmaxepy):
		self.schedule = os.getenv("HOME") + '/.tvmaxe/schedule'
		self.tvmaxepy = tvmaxepy
		self.donejobs = []
		Daemon.__init__(self, "/tmp/tvmaxed.pid")
		
	def run(self):
		os.chdir(os.path.abspath(os.path.dirname(tvmaxepy)))
		while True:
			fh = open(self.schedule, 'rb')
			data = pickle.load(fh)
			fh.close()
			now = datetime.datetime.now()
			now = (now.hour, now.minute, now.day, now.month, now.year)
			for x in data:
				ceas = data[x]['time']
				ceas = (ceas.hour, ceas.minute, ceas.day, ceas.month, ceas.year)
				if now == ceas:
					if not x in self.donejobs:
						doExec = False
						try:
							text = data[x]['name'] + ' is about to start on ' + data[x]['channel'].name + '. Play it now with TV-Maxe?'
							yesno = subprocess.Popen(['zenity', '--question', '--text=' + text])
							yesno.wait()
							if yesno.poll() != 1:
								doExec = True
						except:
							doExec = True
							
						if doExec:
							s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
							for i in range(1, 100):		# try to see if we can communicate with an opened TV-Maxe first
								try:
									s.connect('\0tvmaxe' + str(i))
									s.settimeout(2)
									break
								except:
									continue
							try:
								if s.recv(1024) != 'TVMAXE':
									raise Exception("This ain't TV-Maxe")
								s.send('playtv' + chr(0x1d) + data[x]['channel'].id)
								if s.recv(1024) != 'OK':
									raise Exception("Something gone wrong...")
							except:
								cwd = os.getcwd()
								os.chdir(os.path.dirname(self.tvmaxepy))
								subprocess.Popen([sys.executable, self.tvmaxepy, '--start-channel', data[x]['channel'].id])
								os.chdir(cwd)
						self.donejobs.append(x)
			time.sleep(10)

if __name__ == "__main__":
	try:
		tvmaxepy = sys.argv[1]
		action = sys.argv[2]
	except:
		print "ERROR: Invalid arguments"
		sys.exit(0)
	daemon = TVMaxe_d(tvmaxepy)
	daemon.tvmaxepy = tvmaxepy
	
	if action == 'start':
		daemon.start()
	elif action == 'stop':
		daemon.stop()
	elif action == 'restart':
		daemon.restart()
	else:
		print "ERROR: Invalid action"
		sys.exit(0)
