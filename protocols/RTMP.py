import os, subprocess, tempfile, threading, gobject, time, random
import SocketServer, SimpleHTTPServer

def which(program):
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
    def __init__(self, temp):
        self.temp = temp
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

class Protocol:
    def __init__(self, play_media, stop_media):
        self.play_media = play_media
        self.stop_media = stop_media
        self.stopped = False
        self.params = {}
        self.progress = -1
        self.rtmpdump = None
        self.s = None
        self.outport = None
        self.temp = tempfile.mktemp()
        if not which('rtmpdump'):
            self.protocols = []
        else:
            self.protocols = ['rtmp://', 'rtmpt://', 'rtmpe://', 'rtmpte://', 'rtmps://']

    def play(self, url, params = {}):
        self.stopped = False
        self.progress = -1
        os.mkfifo(self.temp)
        exe = ['rtmpdump', '-v', '-r']
        exe.append(url)
        if url in params:
            params = params[url].split()
            for x in params:
                exe.append(x)
        exe.append('-o')
        exe.append(self.temp)
        print ' '.join(exe)
        self.rtmpdump = subprocess.Popen(exe, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.progress = 0
        threading.Thread(target=self.startmp).start()

    def startmp(self):
        line = self.rtmpdump.stderr.readline()
        while line:
            if 'Connected...' in line:
                break
            line = self.rtmpdump.stderr.readline()
        self.s = Server(self.temp)
        if not self.outport:
            self.outport = random.randint(9000, 9999)
        time.sleep(5)
        threading.Thread(target=self.s.start, args=(self.play_url, self.outport)).start()

    def play_url(self, url):
        self.play_media(url)
        threading.Thread(target=self.checkrun).start()

    def checkrun(self):
        while self.rtmpdump.poll() == None:
            if not self.stopped:
                time.sleep(0.1)
            else:
                return
            if not self.rtmpdump:
                return
        self.stop()
        print 'RTMP Error'
        gobject.idle_add(self.stop_media, "RTMP Error")

    def stop(self):
        self.stopped = True
        if self.s:
            self.s.stop()
        if os.path.exists(self.temp):
            os.remove(self.temp)
        if self.rtmpdump:
            try:
                os.kill(self.rtmpdump.pid, 9)
                self.rtmpdump = None
            except:
                pass
        self.progress = -1

    def quit(self):
        self.stopped = True
        if self.s:
            self.s.stop()
        if os.path.exists(self.temp):
            os.remove(self.temp)
        if self.rtmpdump:
            try:
                os.kill(self.rtmpdump.pid, 9)
                self.rtmpdump = None
            except:
                pass
        self.progress = -1
