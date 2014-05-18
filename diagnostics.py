#!/usr/bin/python2
import os
import sys
import threading
import socket
import gtk
import gobject
import subprocess
import urllib2
import tools
import ffmpegutils
from time import strftime

protocols_dir = os.getcwd() + '/protocols/'
sys.path.append(protocols_dir)


class Diagnostics:
    def __init__(self, gui):
        self.gui = gui
        self.running = False
        self.settingsManager = None

    def show(self):
        self.gui.get_object('diag_waiting_img').hide()
        self.gui.get_object('diag_waiting_txt').hide()
        self.gui.get_object('diagnostics_w').set_visible(True)
        self.gui.get_object('diagnostics_w').present()
        self.gui.get_object('diag_desc').set_markup(
            """<b>Informations</b>\n\n""" +
            """Click on an item in the list to get informations about it."""
        )

    def close(self):
        if self.running:
            return
        self.gui.get_object('diagnostics_store').clear()
        self.gui.get_object('diagnostics_w').hide()

    def run(self):
        if self.running:
            return
        self.gui.get_object('diag_closebtn').set_sensitive(False)
        self.gui.get_object('diag_run').set_sensitive(False)
        self.gui.get_object('diag_waiting_img').set_from_file('wait.gif')
        self.gui.get_object('diag_waiting_img').show()
        self.gui.get_object('diag_waiting_txt').show()
        self.gui.get_object('diagnostics_store').clear()

        self.add_success('Diagnostics started at ' + strftime("%H:%M:%S"), '')
        self.running = True
        self.test_number = -1
        threading.Thread(target=self.do_next_test).start()

    def do_next_test(self):
        self.test_number += 1
        tests = [self.test_tvmaxeorg, self.test_ports, self.test_petrodava,
                 self.test_sopcast, self.test_rtmpdump, self.test_backends,
                 self.test_de, self.test_irw, self.test_ffmpeg]
        if not self.test_number == len(tests):
            try:
                tests[self.test_number]()
            except:
                self.do_next_test()
        else:
            print('Diagnostics finished.')
            gobject.idle_add(self.done_tests)
            return

    def show_details(self, iter):
        title = self.gui.get_object('diagnostics_store').get_value(iter, 1)
        message = self.gui.get_object('diagnostics_store').get_value(iter, 2)
        self.gui.get_object('diag_desc').set_markup(
            "<b>{0}</b>\n\n{1}".format(title, message)
        )

    def add_success(self, message, details):
        gobject.idle_add(self.add_success_main, message, details)

    def add_success_main(self, message, details):
        icon = self.gui.get_object('diagnostics_w').render_icon(
            gtk.STOCK_YES, gtk.ICON_SIZE_MENU
        )
        self.gui.get_object('diagnostics_store').append(
            [icon, message, details]
        )

    def add_warning(self, message, details):
        gobject.idle_add(self.add_warning_main, message, details)

    def add_warning_main(self, message, details):
        icon = self.gui.get_object('diagnostics_w').render_icon(
            gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU
        )
        self.gui.get_object('diagnostics_store').append(
            [icon, message, details]
        )

    def add_error(self, message, details):
        gobject.idle_add(self.add_warning_main, message, details)

    def add_error_main(self, message, details):
        icon = self.gui.get_object('diagnostics_w').render_icon(
            gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU
        )
        self.gui.get_object('diagnostics_store').append(
            [icon, message, details]
        )

    def done_tests(self):
        self.gui.get_object('diag_closebtn').set_sensitive(True)
        self.gui.get_object('diag_run').set_sensitive(True)
        self.gui.get_object('diag_waiting_img').hide()
        self.gui.get_object('diag_waiting_txt').hide()
        self.running = False

        self.add_success('Tests finished.', '')

    """ ------------------------------ TESTS ----------------------------- """
    def test_tvmaxeorg(self):
        try:
            data = urllib2.urlopen('http://tv-maxe.org/hello.txt').read()
            if data == 'hi there!\n':
                self.add_success('Internet connection OK',
                                 "tv-maxe.org was successfully contacted. "
                                 "Loading channelists and TV guides should "
                                 "work properly.")
            else:
                self.add_warning('Unexpected data',
                                 "tv-maxe.org could be contacted, but the "
                                 "received data is invalid. Internet "
                                 "connection may not work properly.")
        except:
            self.add_error('Cannot connect to host',
                           "Couldn't reach tv-maxe.org. Please check your "
                           "internet connection.")
        self.do_next_test()

    def test_ports(self):
        ports = []
        fails = []

        # check for binding ports
        error = False
        if self.settingsManager.staticports:
            ports.append(self.settingsManager.inport)
            ports.append(self.settingsManager.outport)
        else:
            for p in range(9000, 10000):
                ports.append(p)

        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('', port))
                s.close()
            except Exception:
                fails.append(str(port))
                error = True

        # check for sopcast ports
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(('broker.sopcast.com', 3912))
            s.shutdown(2)
        except:
            self.add_warning('Port 3912 error',
                             "Port 3912 cannot be reached. SopCast streams "
                             "may be unavailable.")
            fails.append('3912')
            error = True

        # check for RTMP ports
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(('s3b78u0kbtx79q.cloudfront.net', 1935))
            s.shutdown(2)
        except:
            self.add_warning('Port 1935 error',
                             "Port 3915 cannot be reached. RTMP streams may "
                             "be unavailable.")
            fails.append('1935')
            error = True

        # check for RTSP ports
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(('stream.the.sk', 554))
            s.shutdown(2)
        except:
            self.add_warning('Port 554 error',
                             "Port 554 cannot be reached. RTSP streams may "
                             "be unavailable.")
            fails.append('554')
            error = True

        if error:
            self.add_warning('Some ports are unavailable',
                             "The following ports were found with problems. "
                             "Please make sure that there's no other "
                             "applications using this ports:\n\n{0}\n\n"
                             "Tip: you could use Petrodava to bypass port "
                             "restrictions.".format('\n'.join(fails)))
        else:
            self.add_success('All required ports seems to be ok',
                             "Seems that all the required ports are free "
                             "and also you don't have any restrictions for "
                             "ports from outside.")

        self.do_next_test()

    def test_sopcast(self):
        variants = ['sp-sc', 'sp-sc-auth']
        for sp in variants:
            try:
                p = subprocess.Popen(
                    sp,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                p.wait()
                if p.poll() == 11:
                    self.add_success('SopCast is available',
                                     "SopCast binary was found and seems to "
                                     "work fine.")
                else:
                    self.add_error('SopCast failed to run',
                                   "SopCast binary was found but failed to "
                                   "run. Please run {0} from Terminal for "
                                   "more details.".format(sp))
                self.do_next_test()
                return
            except:
                pass

        self.add_warning('SopCast doesn\'t seems to be installed',
                         "SopCast binary not found. sop:// streams will not "
                         "be available.")
        self.do_next_test()

    def test_rtmpdump(self):
        try:
            p = subprocess.Popen(
                'rtmpdump',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p.wait()
            if p.poll() == 1:
                out = p.stderr.read()
                if not 'Handshake 10 support' in out:
                    self.add_warning('RTMPDump: FP 10 patch not present',
                                     "FlashPlayer 10 Handshake patch not "
                                     "found in RTMPDump. "
                                     "Some streams may not work properly.")
                else:
                    self.add_success('RTMPDump is available',
                                     "RTMPDump is installed and it's working "
                                     "properly")
            else:
                self.add_warning('RTMPDump failed to run',
                                 "rtmpdump was found, but failed to run. "
                                 "Please run rtmpdump from terminal for more "
                                 "details.")
        except:
            self.add_warning("RTMPDump doesn't seems to be installed.",
                             "rtmpdump not found. RTMP streams will be "
                             "unavailable.")

        self.do_next_test()

    def test_backends(self):
        found = 0
        try:
            import gst
            import pygst
            found += 1
            self.add_success('PyGST is available',
                             "PyGST was found and GStreamer should be "
                             "available in TV-Maxe.")
        except:
            self.add_warning('PyGST cannot be imported',
                             "Seems that GStreamer is either not installed or "
                             "the corresponding Python bindings are not "
                             "available. Please install proper packages from "
                             "your distribution repositories if you want "
                             "GStreamer support in TV-Maxe.")

        try:
            import vlc
            try:
                v = vlc.libvlc_get_version().split()[0]
                if int(v.replace('.', '')) < 110:
                    self.add_warning("Old libVLC",
                                     "Your VLC installation is old. At least "
                                     "version 1.1.0 is required for TV-Maxe "
                                     "to work with VLC backend.")
                else:
                    found += 1
                    self.add_success('VLC is available',
                                     "VLC was found in your system and seems "
                                     "to be fully functional.")
            except:
                self.add_warning('Couldn\'t determine VLC version',
                                 "VLC was found, but its version couldn't be "
                                 "determined. VLC backend may not work.")
        except:
            self.add_warning('VLC was not found',
                             "libVLC was not found; playing streams using "
                             "VLC-tvmx backend will not be available.")

        try:
            p = subprocess.Popen(
                'mplayer',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p.wait()
            if not p.poll():
                found += 1
                self.add_success(
                    'MPlayer is available',
                    "MPlayer was found and should be available as TV-Maxe "
                    "backend."
                )
            else:
                self.add_warning('MPlayer error',
                                 "MPlayer was found but doesn't seems to be "
                                 "working. Please run mplayer from Terminal "
                                 "for more details.")
        except:
            self.add_warning('MPLayer not found',
                             "MPlayer was not found; playing streams using "
                             "MPlayer as backend will not be available.")

        if not found:
            self.add_error('No backend available',
                           "No backend found. Playing streams will not work.")
        self.do_next_test()

    def test_de(self):
        de = tools.guess_de()
        if de:
            self.add_success('Desktop environment detected as {0}'.format(de),
                             '')
        else:
            self.add_warning('Desktop environment couldn\'t be detected.',
                             "Auto power off feature may not work.")

        self.do_next_test()

    def test_irw(self):
        try:
            subprocess.Popen(
                'irw',
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.add_success(
                'LIRC was found',
                "LIRC was found installed in your system. Please configure "
                "your IR remote controller if you want to use it with "
                "TV-Maxe.")
        except:
            self.add_warning('LIRC was not found',
                             "IR remote support is disabled. Please install "
                             "LIRC if you got an IR remote controller and you "
                             "want to use it with TV-Maxe.")

        self.do_next_test()

    def test_ffmpeg(self):
        error = False
        try:
            subprocess.Popen(
                'ffmpeg',
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except:
            self.add_error(
                'FFMPEG not available',
                'FFMPEG doesn\'t seems to be installed. '
                'Please install it and make sure that the binary is located '
                'in one of the $PATH directories.')
            error = True

        if not error:
            mp3encoder = ffmpegutils.get_mp3_encoder()
            print(mp3encoder)

        self.do_next_test()

    def test_petrodava(self):
        from Petrodava import PetrodavaPacket
        host = self.settingsManager.getPetrodavaServer()
        port = self.settingsManager.getPetrodavaPort()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
        except:
            self.add_error(
                "Cannot connect to Petrodava",
                "TV-Maxe couldn't connect to Petrodava. This could be because "
                "of your network conenction or the Petrodava servers are down."
            )

        p = PetrodavaPacket()
        p.command = "OHAI"
        p.data = 'test' + chr(0x00) + 'test'
        s.sendall(p.encode())

        header_check = s.recv(4)
        if header_check == 'TVMX':
            self.add_success(
                "Petrodava is working",
                "Your connection with Petrodava server is working. "
                "To connect via Petrodava please enable the option in "
                "TV-Maxe's settings dialog."
            )
        else:
            self.add_error(
                "Petrodava is not working",
                "TV-Maxe connected to Petrodava, but received an invalid "
                "response."
            )

        self.do_next_test()
