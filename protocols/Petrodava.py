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

HOST = 'localhost'    # The remote host
PORT = 8080           # The same port as used by the server


class PetrodavaPacket(object):
    """Format of a Petrodava packet (a "-" equals one byte)
    +----+-+----+-+--+-+--------------------------------+
    |TVMX+0+COMM+0+SZ+0+Payload                         +

    where:
    TVMX - header of the packet
    0 - separator (0x00)
    COMM - protocol command
    SZ - size of the payload
    Payload - the data sent via this packet
    """
    def __init__(self):
        self._data = ''
        self._length = 0
        self._command = 'NONE'
        self.request = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self._length = len(value)

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
                struct.pack('!H', len(self.data)) + chr(0x00) + self.data
        return pdata

    def decode(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(ValueError, "This doesn't seems to be a Petrodava packet")

        self._length = struct.unpack('!H', rawdata[10:12])[0]
        self._command = rawdata[5:9]
        self._data = rawdata[13:self._length]

    def decode_partial(self, rawdata):
        if not rawdata.startswith('TVMX'):
            raise(ValueError, "This doesn't seems to be a Petrodava packet")

        self._length = struct.unpack('!H', rawdata[10:12])[0]
        self._command = rawdata[5:9]


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
                fh = open('/tmp/petrodava', 'rb')
                while True:
                    byte = fh.read(2048)
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
        self.protocols = ['*']

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def play(self, url, params={}):
        if os.path.exists('/tmp/petrodava'):
            os.remove('/tmp/petrodava')
        self.s.connect((HOST, PORT))
        threading.Thread(target=self.startmp, args=(url,)).start()

    def startmp(self, url):
        self.httpsrv = Server()
        self.progress = 0
        p = PetrodavaPacket()
        p.command = "OHAI"
        p.data = ''

        print 'Sending', len(p.encode()), 'bytes...'
        self.s.send(p.encode())

        recvp = PetrodavaPacket()
        recvp.decode_partial(self.s.recv(13))
        if recvp.length:
            self.s.recv(recvp.length)

        print 'Received', recvp.command

        if recvp.command == "HI00":
            p = PetrodavaPacket()
            p.command = "CONN"
            p.data = url
            self.s.sendall(p.encode())

            recvp = PetrodavaPacket()
            recvp.decode_partial(self.s.recv(13))
            if recvp.length:
                recvp.data = self.s.recv(recvp.length)

            if recvp.command == 'WAIT':
                while True:
                    recvp = PetrodavaPacket()
                    recvp.decode_partial(self.s.recv(13))
                    if recvp.length:
                        recvp.data = self.s.recv(recvp.length)

                    if recvp.command == 'WAIT':
                        self.progress == int(recvp.data)
                    elif recvp.command == 'DATA':
                        if self.progress != -1:
                            self.progress = -1
                            threading.Thread(target=self.httpsrv.start, args=(self.play_media, )).start()

                        if not os.path.exists('/tmp/petrodava'):
                            os.mkfifo('/tmp/petrodava')
                        fh = open('/tmp/petrodava', 'wb')
                        fh.write(recvp.data)
                        fh.close()

            else:
                print recvp.command

    def stop(self):
        pass

    def quit(self):
        pass
