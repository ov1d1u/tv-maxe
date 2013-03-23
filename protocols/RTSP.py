import os, subprocess, threading, gobject, time, random, ctypes
import SocketServer, SimpleHTTPServer
from Queue import Queue, Empty

class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def do_GET(self):
                self.server.abort = False
		self.send_response(200)
		self.end_headers()
		q = Queue()
		t = threading.Thread(target=self.enqueue, args=(q, ))
		t.start()
		while True:
                        try:
                                byte = q.get()
                        except:
                                continue
			try:
				self.wfile.write(byte)
			except:
                                self.server.abort = True
                                print 'Ooops, something went wrong :)'
				return
			
	def enqueue(self, q):
                while True:
			byte = self.server.stdout.read(2048)
                        q.put(byte)
                        if self.server.abort:
                                return

class Server:
	def __init__(self, stdout):
		self.stdout = stdout
		self.port = random.randint(9000, 9999)
		self.httpd = None
		
	def start(self, callback):
		self.httpd = SocketServer.ThreadingTCPServer(('', self.port), Proxy)
		self.httpd.stdout = self.stdout
		self.httpd.abort = False
		threading.Thread(target=self.httpd.serve_forever).start()
		time.sleep(3)
		gobject.idle_add(callback, 'http://localhost:' + str(self.port))
		
	def stop(self):
		if self.httpd:
			self.httpd.shutdown()
			self.httpd.abort = True
			print 'Stopped server'
    
class Protocol:
	def __init__(self, play_media, stop_media):
		self.play_media = play_media
		self.stop_media = stop_media
		self.stopped = False
		self.params = {}
		self.progress = -1
		self.ffmpeg = None
		self.error = None
		self.s = None
        	self.protocols = ['rtsp://', 'mms://', 'mmsh://']

	def play(self, url, params = {}):
                self.error = False
		self.progress = -1
		self.stopped = False
		if url.startswith('mms://'):
			url = url.replace('mms://', 'mmsh://')
			exe = ['ffmpeg', '-y', '-i', url, '-acodec', 'copy', '-vcodec', 'copy', '-f', 'flv', '-']
		else:
			exe = ['ffmpeg', '-y', '-i', url,  '-acodec', 'libmp3lame', '-ar', '44100', '-vcodec', 'copy', '-f', 'flv', '-']
		print ' '.join(exe)
		self.ffmpeg = subprocess.Popen(exe, stdout=subprocess.PIPE)
		self.progress = 0
		threading.Thread(target=self.startmp).start()
		
	def startmp(self):
		self.progress = 0
              	self.s = Server(self.ffmpeg.stdout)
               	threading.Thread(target=self.s.start, args=(self.play_url, )).start()
		
	def play_url(self, url):
                print 'play media', url
                self.play_media(url)
                threading.Thread(target=self.checkrun).start()
		
	def checkrun(self):
		if not self.ffmpeg:
			return
		while self.ffmpeg.poll() == None:
			if not self.stopped:
				time.sleep(0.1)
			else:
				return
			if not self.ffmpeg:
				return
		self.error = True
		print 'RTSP Error'
		gobject.idle_add(self.stop_media, "RTSP Error")
			
	def stop(self):
		self.stopped = True
		if self.s:
			self.s.stop()
			self.s = None
		if self.ffmpeg:
			try:
				os.kill(self.ffmpeg.pid, 9)
				self.ffmpeg = None
			except:
				pass
		self.progress = -1
		
	def quit(self):
		self.stopped = True
		if self.s:
			self.s.stop()
			self.s = None
		if self.ffmpeg:
			try:
				os.kill(self.ffmpeg.pid, 9)
				self.ffmpeg = None
			except:
				pass
		self.progress = -1
