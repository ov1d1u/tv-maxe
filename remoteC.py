from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading, gobject, urllib2, json, urlparse

interface_version = 0.1

class MyHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if 'favicon.ico' in self.path:
			return
		self.tvchannels = self.server.chlist('tv')
		self.radiochannels = self.server.chlist('radio')
		self.epg = None
		try:
			self.server.info()['tvguide'](self.server.info()['chid'], self.setCurrentEPG)
		except:
			pass
		try:
			# JSON Interface
			if 'json?' in self.path:
				parsed = urlparse.urlparse(self.path)
				urldata = urlparse.parse_qs(parsed.query)
				self.send_response(200)
				self.send_header('Content-type', 'text/plain')
				self.end_headers()
				if (urldata.has_key('info')):
					pagedata = {'appname':'tvmaxe', 'version':str(self.server.tvmaxe.getVersion()), 'protoversion':str(interface_version)}
					self.wfile.write(json.dumps(pagedata))
					return
				if (urldata.has_key('get_channels')):
					print self.tvchannels
					return
				self.wfile.write(json.dumps({'error':'No action defined.'}))
				return
			# end of JSON Interface
			if 'switch?' in self.path:
				self.send_response(303)
				self.send_header('Location', '/')
				self.end_headers()
				url = self.path.split('switch?url=')
				url = urllib2.unquote(url[1])
				gobject.idle_add(self.server.chchannel, url)
				self.server.lastChannel = url
				return
			if 'volume?' in self.path:
				self.send_response(303)
				self.send_header('Location', '/')
				self.end_headers()
				if 'plus' in self.path:
					gobject.idle_add(self.server.volume, None, None, 0.2)
				elif 'minus' in self.path:
					gobject.idle_add(self.server.volume, None, None, -0.2)
				elif 'mute' in self.path:
					gobject.idle_add(self.server.mute)
				return
			if 'stop' in self.path:
				self.send_response(303)
				self.send_header('Location', '/')
				self.end_headers()
				gobject.idle_add(self.server.stop, None)
				return
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write("""
			<html>
				<head>
					<title>TV-MAXE remote control</title>
				</head>
				<body>
				<div align="center">
					<img src="http://www.pymaxe.com/tvmaxe/tvmaxe.jpg" alt="tvmaxe" border="0"/><br/>
					<b>TV-MAXE remote control</b><br/>""")
			if self.server.channelinfo():
				self.wfile.write('<b>'+ self.server.channelinfo()['status'] +'</b><br/> ')
				if self.epg:
					self.wfile.write('<i>' + self.epg + '</i><br/>')
			self.wfile.write("""
					<br/>
					<a href="volume?mute">Mute</a> | <a href="volume?minus">Volume -</a> | <a href="volume?plus">Volume +</a><br/>
					<a href="stop">STOP</a>
					<hr/>
					<b>TV Channels: </b>
					<form name="tvchannels" method="get" action="switch">
					<select name="url" onchange="this.form.submit();">
					<option></option>""")
			sort = sorted(self.tvchannels, key=self.tvchannels.get)
			for x in sort:
				if self.server.lastChannel and self.server.lastChannel == x:
					self.wfile.write('<option value="' + x +'" selected="selected">' + self.tvchannels[x] + '</option>')
				else:
					self.wfile.write('<option value="' + x +'">' + self.tvchannels[x] + '</option>')
			self.wfile.write("""</select></form>
			<b>Radio Channels: </b>
					<form name="radiochannels" method="get" action="switch">
					<select name="url" onchange="this.form.submit();">
					<option></option>""")
			sort = sorted(self.radiochannels, key=self.radiochannels.get)
			for x in sort:
				if self.server.lastChannel and self.server.lastChannel == x:
					self.wfile.write('<option value="' + x +'" selected="selected">' + self.radiochannels[x] + '</option>')
				else:
					self.wfile.write('<option value="' + x +'">' + self.radiochannels[x] + '</option>')	
			self.wfile.write("""</select></form>
				</div>
				</body>
			</html>""")
			return
		except Exception, e:
			print e
			self.send_error(500, 'Internal server error')  

	def do_POST(self):
		return
		
	def setCurrentEPG(self, name, chname):
		self.epg = name
    
class HTTPRemoteControl:
	def __init__(self, tvmaxe, **funcs):
		self.tvmaxe = tvmaxe
		self.chchannel = funcs['chchannel']
		self.volume = funcs['volume']
		self.mute = funcs['mute']
		self.stop = funcs['stop']
		self.channelinfo = funcs['channelinfo']
		
	def start(self, port):
		threading.Thread(target=self.start_server, args=(port, )).start()
		
	def start_server(self, port):
		self.server = HTTPServer(('', port), MyHandler)
		self.server.tvmaxe = self.tvmaxe
		self.server.chlist = self.tvmaxe.getChannelList
		self.server.chchannel = self.chchannel
		self.server.volume = self.volume
		self.server.mute = self.mute
		self.server.stop = self.stop
		self.server.channelinfo = self.channelinfo
		self.server.lastChannel = None
		self.server.serve_forever()
		
	def stop(self):
		if hasattr(self, 'server'):
			self.server.socket.close()