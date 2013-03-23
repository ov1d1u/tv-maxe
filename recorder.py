import os, subprocess, threading, gobject, time, random, ctypes, tempfile
import SocketServer, SimpleHTTPServer

class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
                if not os.path.exists(self.server.temp):
                        self.send_response(404)
                        self.end_headers()
                        return
                self.send_response(200)
                self.end_headers()
                fh = open(self.server.temp, 'rb')
                byte = fh.read(1024)
                while byte != "":
                        try:
                                self.wfile.write(byte)
                        except:
                                return
                        byte = fh.read(1024)

class Server:
	def __init__(self, tempfile):
		self.temp = tempfile
		self.httpd = None
		
	def start(self, callback, port):
		self.httpd = SocketServer.ThreadingTCPServer(('', port), Proxy)
		self.httpd.temp = self.temp
		threading.Thread(target=self.httpd.serve_forever).start()
		gobject.idle_add(callback, 'http://localhost:' + str(port))
		
	def stop(self):
		if self.httpd:
			self.httpd.shutdown()
			print 'Stopped server'
			
	def __del__(self):
		self.stop()

class Recorder:
	def __init__(self, callback, xid, mp, settingsManager):
		self.name = 'Recorder'
		self.callback = callback
		self.xid = xid
		self.mprunning = False
		self.error = False
		self.imagesink = None
		self.ffmpeg = None
		self.forceaspect = True
		self.recQuality = 5
		self.mediaPlayer = mp
		self.settingsManager = settingsManager
		self.saveAs = os.getenv('HOME') + '/recording.avi'
		
	def play(self, url):
		print '--------------- Recording stream', url
		self.tmpfile = tempfile.mkstemp()[1]
		os.unlink(self.tmpfile)
		os.mkfifo(self.tmpfile)
		threading.Thread(target=self.playResume, args=(url, )).start()
		
	def playResume(self, url):
		time.sleep(2)
		self.saveAs = self.saveAs.replace('file://', '')
		exe = ['ffmpeg', '-y', '-i', url, '-acodec', 'copy', '-vcodec', 'copy', '-f', self.settingsManager.getFormat(), self.tmpfile,
				'-acodec', self.settingsManager.getACodec(), '-ab', '128k', '-vcodec', self.settingsManager.getVCodec(), 
				'-qscale', str(self.settingsManager.getRecQuality()), '-f', self.settingsManager.getFormat(), os.path.splitext(self.saveAs)[0]]
		print ' '.join(exe)
		self.ffmpeg = subprocess.Popen(exe, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		self.mprunning = True
		self.progress = 0
		threading.Thread(target=self.startmp).start()
		
	def startmp(self):
		self.progress = 0
              	self.s = Server(self.tmpfile)
		self.outport = random.randint(9000, 9999)
               	threading.Thread(target=self.s.start, args=(self.play_url, self.outport)).start()
		
	def play_url(self, url):
		self.mediaPlayer.play(url)
		
	def pause(self):
		self.mediaPlayer.pause(url)
			
	def stop(self):
		self.mprunning = False
		if self.ffmpeg:
			try:
				self.ffmpeg.stdin.write('q')
			except:
				pass
		if self.ffmpeg:
			while self.ffmpeg.poll() == None:
				time.sleep(0.5)
		self.ffmpeg = None
		if self.s:
			self.s.stop()
			self.s = None
		if os.path.exists(self.tmpfile):
			os.unlink(self.tmpfile)
		self.mediaPlayer.stop()
	
	def volume(self, value):
		self.mediaPlayer.volume(value)
			
	def adjustImage(self, b, c, s):
		self.mediaPlayer.adjustImage(b, c, s)

	def OSD(self, text):
		self.mediaPlayer.OSD(text)
	
	def setRatio(self, ratio):
		self.mediaPlayer.setRatio(ratio)
			
	def getStatus(self):
		return self.mediaPlayer.getStatus()
			
	def getTime(self):
		return self.mediaPlayer.getTime()
	
	def seek(self, t):
		self.mediaPlayer.seek(t)
	
	def isPlaying(self):
		return self.mediaPlayer.isPlaying()
	
	def quit(self):
		self.stop()
		
	def adjustTime(self, seconds):
		threading.Thread(target=self.doAdjust, args=(seconds,)).start()

	def doAdjust(self, seconds):
		if not os.path.exists(os.path.splitext(self.saveAs)[0]):
			return
		self.tempname = os.path.splitext(self.saveAs)[0] + '_'
		os.rename(os.path.splitext(self.saveAs)[0], self.tempname)
		exe = ['ffmpeg', '-y', '-i', self.tempname, '-acodec', 'copy', '-vcodec', 'copy', '-t', str(seconds), '-f', self.settingsManager.getFormat(), self.saveAs]
		print ' '.join(exe)
		self.ffmpeg = subprocess.Popen(exe, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		self.ffmpeg.wait()
		if os.path.getsize(self.saveAs) < 10240:	# workaround if conversion failed
			os.unlink(self.saveAs)
			os.rename(self.tempname, self.saveAs)
		else:
			os.unlink(self.tempname)

	def quit(self):
		if hasattr(self, 'ffmpeg'):
			try:
				self.ffmpeg.kill()
				os.unlink(self.tempname)
			except:
				pass
