import socket
import struct
import threading
import SocketServer
import SimpleHTTPServer
import os
import random
import time
import gobject
import tempfile
from Queue import Queue, Empty

HOST = '162.243.228.197'    # The remote host
PORT = 8080           # The same port as used by the server
HEADER_LENGTH = 52

data_queue = Queue()


class PetrodavaPacket(object):
    """Format of a Petrodava packet (a "-" equals one byte)
    +----+-+----+-+----+-+------------------------------------+-+-------+
    |TVMX+0+COMM+0+SIZE+0+UUID--------------------------------+0+Payload+

    where:
    TVMX - header of the packet
    0 - separator (0x00)
    COMM - protocol command
    SZ - size of the payload
    UUID - unique identifier of the session
    Payload - the data sent via this packet
    """
    def __init__(self):
        self._data = ''
        self._length = 0
        self._command = 'NONE'
        self._uid = '00000000-0000-0000-0000-000000000000'
        self.request = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self._length = len(value)

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value

    @property
    def length(self):
        return self._length

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, cmd):
        if not len(cmd) == 4:
            raise(ValueError, "The command length must be 4 characters")
        self._command = cmd

    def encode(self):
        pdata = 'TVMX' + chr(0x00) + self.command + chr(0x00) + \
                struct.pack('!I', len(self.data)) + chr(0x00) + \
                self._uid + chr(0x00) + self.data
        return pdata

    def decode(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(ValueError, "This doesn't seems to be a Petrodava packet")

        self._length = struct.unpack('!I', rawdata[10:14])[0]
        self._command = rawdata[5:9]
        self._uid = rawdata[15:51]
        self._data = rawdata[52:52 + self._length]

    def decode_partial(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(ValueError, "This doesn't seems to be a Petrodava packet")

        self._length = struct.unpack('!I', rawdata[10:14])[0]
        self._command = rawdata[5:9]
        self._uid = rawdata[15:51]


class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.server.abort = False
        self.send_response(200)
        self.end_headers()
        q = Queue()
        t = threading.Thread(target=self.enqueue, args=(q, ))
        t.start()
        while True:
            print '1'
            try:
                byte = q.get()
            except:
                continue
            try:
                self.wfile.write(byte)
            except:
                self.server.abort = True
                print 'Ooops, something went wrong :('
                return

    def enqueue(self, q):
                # fh = open('/tmp/petrodava', 'rb')
                # fh = os.fdopen(os.open('/tmp/petrodava', os.O_BINARY))
                while True:
                    print '2'
                    byte = data_queue.get() # fh.read(65536)
                    q.put(byte)
                    if self.server.abort:
                        fh.close()
                        return


class Server:
    def __init__(self):
        self.port = random.randint(9000, 9999)
        self.httpd = None

    def start(self, callback):
        self.httpd = SocketServer.ThreadingTCPServer(('', self.port), Proxy)
        self.httpd.abort = False
        threading.Thread(target=self.httpd.serve_forever).start()
        time.sleep(3)
        gobject.idle_add(callback, 'http://localhost:' + str(self.port))

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.abort = True
            print 'Stopped server'


class SocketConnection:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.q = Queue()
        self.connected = False
        self.listener_running = False
        self.sender_running = False
        self.uid = '00000000-0000-0000-0000-000000000000'

        self.start()

    def start(self):
        self.s.connect((HOST, PORT))
        self.connected = True

        threading.Thread(target=self.listener, args=()).start()
        threading.Thread(target=self.sender, args=()).start()

    def listener(self):
        if self.listener_running:
            print 'Listener thread already running, abort...'
            return

        self.listener_running = True

        # do the initial connection
        p = PetrodavaPacket()
        p.command = "OHAI"
        p.data = ''
        self.send_packet(p)

        while True:
            print '3'
            header = self.s.recv(HEADER_LENGTH)
            while len(header) < HEADER_LENGTH:
                print '4'
                header += self.s.recv(1)

            recvp = PetrodavaPacket()
            recvp.decode_partial(header)
            data_length = recvp.length
            recvp.data = self.s.recv(data_length)
            if data_length:
                while len(recvp.data) < data_length:
                    print '5'
                    recvp.data += self.s.recv(1)

            if recvp.command == 'HI00':
                self.uid = recvp.data
                print 'Setting uid: {0}'.format(self.uid)
            if recvp.command == 'WAIT':
                print 'Buffer progress: {0}'.format(recvp.data)
                if 'update_progress' in self.callbacks:
                    self.callbacks['update_progress'](int(recvp.data))
            if recvp.command == 'DATA':
                self.callbacks['write_data'](recvp.data)

    def sender(self):
        if self.sender_running:
            print 'Sender thread already running, abort...'
            return

        self.sender_running = True

        while True:
            print '6'
            p = self.q.get()
            if p.command != 'OHAI' and self.uid == '00000000-0000-0000-0000-000000000000':
                # UID not set yet, try again
                self.q.put(p)
            else:
                print 'Sending packet of type {0} length {1} bytes'.format(p.command, p.length)
                p.uid = self.uid
                self.s.sendall(p.encode())

    def send_packet(self, p):
        if not self.connected:
            threading.Thread(target=self.listener, args=()).start()
        self.q.put(p)


class Protocol:
    def __init__(self, play_media, stop_media):
        print 'Init petrodava...'
        self.play_media = play_media
        self.stop_media = stop_media
        self.stopped = False
        self.params = {}
        self.progress = -1
        self.ffmpeg = None
        self.error = None
        self.httpsrv = None
        self.conn = None
        self.protocols = ['*']

    def play(self, url, params={}):
        self.conn = SocketConnection({
            'update_progress': self.update_progress,
            'write_data': self.write_data
            })

        if os.path.exists('/tmp/petrodava'):
            os.remove('/tmp/petrodava')
        threading.Thread(target=self.startmp, args=(url,)).start()

    def startmp(self, url):
        p = PetrodavaPacket()
        p.command = 'CONN'
        p.data = url
        self.conn.send_packet(p)

    def update_progress(self, progress):
        self.progress = progress

    def write_data(self, data):
        if not self.httpsrv:
            self.httpsrv = Server()
            threading.Thread(target=self.httpsrv.start, args=(self.play_media, )).start()
            self.progress = 0

        # print 'Writing {0} bytes...'.format(len(data))

        if not os.path.exists('/tmp/petrodava'):
            os.mkfifo('/tmp/petrodava')
        data_queue.put(data)

    def stop(self):
        if self.conn:
            p = PetrodavaPacket()
            p.command = 'EXIT'
            self.conn.send_packet(p)
            self.conn = None

    def quit(self):
        if self.conn:
            p = PetrodavaPacket()
            p.command = 'EXIT'
            self.conn.send_packet(p)
            self.conn = None
