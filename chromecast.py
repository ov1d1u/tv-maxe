import threading
import gobject
import socket

pychromecast_available = None
try:
    import pychromecast
    pychromecast_available = True
except:
    print "Pychromecast not available"
    pychromecast_available = False


class ChromecastProvider:
    def __init__(self, tvmx, success_cb=None):
        self.tvmx = tvmx
        self.success_cb = success_cb
        self.devices = []
        self.cast = None

        if pychromecast_available:
            thread = threading.Thread(target=self.search_devices, name="Chromecast finder")
            thread.start()

    def search_devices(self):
        print "Searching for Chromecast devices..."
        self.devices = pychromecast.get_chromecasts_as_dict().keys()
        gobject.idle_add(self.success_cb)

    def connect(self, device_name):
        self.cast = pychromecast.get_chromecast(friendly_name=device_name)

    def play_media(self, url, mimetype='video/mp4'):
        def do_play(url, mimetype):
            self.cast.wait()  # wait for connection, if needed
            local_ip = self._get_local_ip()
            url = url.replace('127.0.0.1', local_ip)
            url = url.replace('localhost', local_ip)
            mc = self.cast.media_controller
            print "Playing {0} to {1} as {2}".format(url, self.cast.device.friendly_name, mimetype)
            mc.play_media(url, 'video/mp4')

        if self.cast:
            play_thr = threading.Thread(target=do_play, args=(url, mimetype))
            play_thr.start()
            return True
        return False

    def stop(self):
        if self.cast:
            mc = self.cast.media_controller
            mc.stop()

    def _get_local_ip(self):
        return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
