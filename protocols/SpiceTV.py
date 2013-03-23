import os, subprocess, tempfile, threading, gtk, gobject, time, random, ConfigParser
import SocketServer, SimpleHTTPServer
import urllib, urllib2, cookielib

cfgfile = os.getenv('HOME') + '/.tvmaxe/spicetv.cfg'
config = ConfigParser.ConfigParser()


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
        self.url = ''
        self.progress = -1
        self.rtmpdump = None
        self.s = None
        self.outport = None
        self.temp = tempfile.mktemp()
        if not which('rtmpdump'):
            self.protocols = []
        else:
            self.protocols = ['spice://']
        # login system
        self.cj = cookielib.CookieJar()
        if not os.path.exists(cfgfile):
            config.add_section('Account')
            config.set('Account', 'username', '')
            config.set('Account', 'password', '')
            with open(cfgfile, 'wb') as configfile:
                config.write(configfile)
        config.read(cfgfile)
        self.username = config.get('Account', 'username')
        self.password = config.get('Account', 'password')
        self.sessionkey = ''

    def play(self, url, params={}):
        self.url = url
        self.params = params
        if self.sessionkey == '':
            if (self.username == '' and self.password == ''):
                gobject.idle_add(self.login)
            else:
                print 'SpiceTV: autologin'
                self.do_login()
        else:
            self.start_play()

    def start_play(self):
        url = self.url.replace('spice://', 'rtmp://')
        params = self.params
        self.stopped = False
        self.progress = -1
        os.mkfifo(self.temp)
        exe = ['rtmpdump', '-v', '-r']
        exe.append(url)
        if self.url in params:
            params = params[self.url].split()
            for x in params:
                x = x.replace("%KEY%", self.sessionkey)
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

    def login(self, error=False):
        gtk.gdk.threads_enter()
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, '')
        dialog.set_markup("""You need a SpiceTV account to watch this channel.
If you don't have one, register for free at
<a href="http://www.spicetv.ro/user/inregistrare">http://www.spicetv.ro/user/inregistrare</a>""")
        if error:
            dialog.set_title('ERROR: INVALID LOGIN')
        else:
            dialog.set_title('SpiceTV authenticating')
        window = dialog.get_content_area()
        username_label = gtk.Label("Username:")
        password_label = gtk.Label("Password:")
        username_entry = gtk.Entry()
        password_entry = gtk.Entry()
        password_entry.set_visibility(False)
        vbox = gtk.VBox()
        hbox1 = gtk.HBox(homogeneous=True)
        hbox1.pack_start(username_label)
        hbox1.pack_start(username_entry)
        hbox2 = gtk.HBox(homogeneous=True)
        hbox2.pack_start(password_label)
        hbox2.pack_start(password_entry)
        vbox.pack_start(hbox1)
        vbox.pack_start(hbox2)
        window.add(vbox)
        window.show_all()
        resp = dialog.run()
        if resp == gtk.RESPONSE_OK:
            self.username = username_entry.get_text()
            self.password = password_entry.get_text()
            gobject.idle_add(dialog.destroy)
            self.do_login()
        else:
            gobject.idle_add(dialog.destroy)
            gobject.idle_add(self.stop_media, "Login canceled")
        gtk.gdk.threads_leave()

    def do_login(self):
        try:
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
            login_data = urllib.urlencode({'email': self.username, 'pass': self.password, 'submit': 'Login'})
            opener.open('http://www.spicetv.ro/user/login', login_data)
            # try a free channel to get the app key
            resp = opener.open("http://www.spicetv.ro/tv-online/inedit-tv")
            htmldata = resp.read()
            gkey = htmldata.split('","')
            gkey2 = gkey[2].split('");')
            self.sessionkey = gkey2[0]
            config.set('Account', 'username', self.username)
            config.set('Account', 'password', self.password)
            with open(cfgfile, 'wb') as configfile:
                config.write(configfile)
            self.start_play()
        except Exception, e:
            print "Login error"
            gobject.idle_add(self.login)

    def cancel_login(self, obj=None, event=None):
        obj.get_toplevel().destroy()
