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

HEADER_LENGTH = 52
CHUNK_DATA_SIZE = 4096
ZERO_UID = '00000000-0000-0000-0000-000000000000'

data_queue = Queue()


class DecodeError(Exception):
    pass


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
        self._uid = ZERO_UID
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
        pdata = 'TVMX' + chr(0x00) + str(self.command) + chr(0x00) + \
                struct.pack('!I', len(self.data)) + chr(0x00) + \
                str(self._uid) + chr(0x00) + str(self.data)
        return pdata

    def decode(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(DecodeError, "This doesn't seems to be a Petrodava packet")

        self._length = struct.unpack('!I', rawdata[10:14])[0]
        self._command = rawdata[5:9]
        self._uid = rawdata[15:51]
        self._data = rawdata[52:52 + self._length]

    def decode_partial(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(DecodeError, "This doesn't seems to be a Petrodava packet")

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
            try:
                byte = q.get()
            except:
                continue
            try:
                self.wfile.write(byte)
            except:
                self.server.abort = True
                self.shutdown()
                print 'Ooops, something went wrong :('
                return

    def enqueue(self, q):
                # fh = open('/tmp/petrodava', 'rb')
                # fh = os.fdopen(os.open('/tmp/petrodava', os.O_BINARY))
                while True:
                    byte = data_queue.get() # fh.read(65536)
                    q.put(byte)
                    if self.server.abort:
                        #fh.close()
                        return


class Server:
    def __init__(self):
        self.port = random.randint(29000, 29999)
        self.httpd = None

    def start(self, callback):
        self.httpd = SocketServer.ThreadingTCPServer(('', self.port), Proxy)
        self.httpd.abort = False
        threading.Thread(target=self.httpd.serve_forever).start()
        print 'Started server at http://localhost:{0}/'.format(self.port)
        time.sleep(3)
        gobject.idle_add(callback, 'http://localhost:{0}'.format(self.port))

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.abort = True
            print 'Stopped server'


class SocketConnection:
    def __init__(self, host, port, user, passw, callbacks):
        self.callbacks = callbacks
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.q = Queue()
        self.connected = False
        self.listener_running = False
        self.sender_running = False
        self.uid = ZERO_UID
        self.host = host
        self.username = user
        self.password = passw
        self.port = int(port)
        self.stop = False

        self.start()

    def start(self):
        print 'Petrodava: connecting to {0}:{1}'.format(self.host, self.port)
        self.s.connect((self.host, self.port))
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
        p.data = self.username + chr(0x00) + self.password
        self.send_packet(p)

        while True:
            header = self.s.recv(HEADER_LENGTH)
            while len(header) < HEADER_LENGTH:
                header += self.s.recv(1)

            try:
                recvp = PetrodavaPacket()
                recvp.decode_partial(header)
                data_length = recvp.length
                if data_length:
                    recvp.data = self.s.recv(data_length)
                    while len(recvp.data) < data_length:
                        left = data_length - len(recvp.data)
                        if left > CHUNK_DATA_SIZE:
                            recvp.data += self.s.recv(CHUNK_DATA_SIZE)
                        elif left > 0:
                            recvp.data += self.s.recv(left)

                if recvp.command == 'HI00':
                    self.uid = recvp.data
                    if self.uid == ZERO_UID:
                        self.callbacks['stop_media']('PETRODAVA LOGIN ERROR')
                        self.stop = True
                    print 'Setting uid: {0}'.format(self.uid)
                if recvp.command == 'WAIT':
                    print 'Buffer progress: {0}'.format(recvp.data)
                    if 'update_progress' in self.callbacks:
                        self.callbacks['update_progress'](int(recvp.data))
                if recvp.command == 'DATA':
                    self.callbacks['write_data'](recvp.data)
                if recvp.command == 'STOP':
                    self.callbacks['stop_media'](recvp.data)
                if recvp.command == 'PING':
                    pong = PetrodavaPacket()
                    pong.command = 'PONG'
                    pong.data = recvp.data
                    self.send_packet(pong)
            except DecodeError, e:
                print 'Decode error'
            except Exception, e:
                print 'Exception occured:', e
                time.sleep(0.01)

            header = ''

            if self.stop:
                print 'STOP {0}'.format(self.uid)
                self.s.close()
                return

    def sender(self):
        if self.sender_running:
            print 'Sender thread already running, abort...'
            return

        self.sender_running = True

        while not self.stop:
            p = self.q.get()
            if p.command != 'OHAI' and self.uid == ZERO_UID:
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

    def close(self):
        print 'Close Connection {0}'.format(self.uid)
        self.s.close()
        self.stop = True
        p = PetrodavaPacket()
        p.command = 'EXIT'
        self.send_packet(p)


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
        self.petrodava_server = ''
        self.petrodava_port = ''
        self.petrodava_username = ''
        self.petrodava_password = ''
        self.protocols = ['*']

    def play(self, url, params={}):
        self.conn = SocketConnection(
            self.petrodava_server,
            self.petrodava_port,
            self.petrodava_username,
            self.petrodava_password,
            {
                'update_progress': self.update_progress,
                'write_data': self.write_data,
                'stop_media': self.stop_petrodava
            })

        threading.Thread(target=self.startmp, args=(url, params)).start()

    def startmp(self, url, params):
        url_params = ''
        if params.has_key(url):
            url_params = params[url]

        p = PetrodavaPacket()
        p.command = 'CONN'
        p.data = url + chr(0x00) + url_params
        self.conn.send_packet(p)

    def update_progress(self, progress):
        self.progress = progress

    def write_data(self, data):
        if not self.httpsrv:
            self.httpsrv = Server()
            threading.Thread(target=self.httpsrv.start, args=(self.play_media, )).start()
            self.progress = 0

        # print 'Writing {0} bytes...'.format(len(data))

        data_queue.put(data)

    def stop(self, error=None):
        self.progress = 0

        p = PetrodavaPacket()
        p.command = 'EXIT'

        if error == '':
            error = None
        if self.conn:
            self.conn.send_packet(p)
            self.conn.close()
            self.conn = None
        if self.httpsrv:
            self.httpsrv.stop()
            self.httpsrv = None

    def stop_petrodava(self, error=None):
        self.progress = 0

        if error == '':
            error = None
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.httpsrv:
            self.httpsrv.stop()
            self.httpsrv = None
        gobject.idle_add(self.stop_media, error)

    def quit(self):
        if self.conn:
            self.conn.close()
            self.conn = None
