import socket, threading, time, gobject

nrcon = 5

class SocketServer:
	def __init__(self, tvmaxe):
		self.tvmaxe = tvmaxe
		self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		for x in range(1, 100):
			try:
				self.s.bind('\0tvmaxe' + str(x))
				break
			except:
				continue
		self.s.setblocking(1)
		self.s.listen(nrcon)
		threading.Thread(target=self.listen).start()
			
	def listen(self):
		self.conn, self.addr = self.s.accept()
		self.conn.send('TVMAXE')
		while True:
			data = self.conn.recv(1024)
			gobject.idle_add(self.execute, data)
			
	def execute(self, line):
		params = line.split(chr(0x1d))
		if params[0] == 'playtv':
			chid = params[1]
			if self.tvmaxe.channels.has_key(chid):
				self.tvmaxe.playChannel(self.tvmaxe.channels[chid])
				self.conn.send('OK')

	def close(self):
		self.s.close()
