import os
import subprocess
import threading
import random


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


class Protocol:
    def __init__(self, play_media, stop_media):
        self.play_media = play_media
        self.stop_media = stop_media
        self.outport = None
        self.player = None
        self.protocols = []
        if which('acestreamplayer'):
            self.protocols = ['acestream://']

    def play(self, url, params={}):
        self.progress = -1
        if not self.outport:
            self.outport = random.randint(9000, 9999)
        dst = '127.0.0.1:{0}'.format(self.outport)
        exe = ['acestreamplayer', '-I', 'dummy', url, '--sout-keep', '--verbose', '2',
                '--sout', '#http{{mux=ts,dst={0}/}}'.format(dst)]
        self.player = subprocess.Popen(
            exe,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        threading.Thread(target=self.startmp, args=(dst, )).start()

    def startmp(self, dst):
        url = 'http://{0}'.format(dst)
        line = self.player.stderr.readline()
        while line:
            if 'IN_MSG_PLAY' in line:
                print('Play: {0}'.format(url))
                self.play_media(url)
            line = self.player.stderr.readline()

    def stop(self):
        if self.player:
            try:
                os.kill(self.player.pid, 9)
                self.player = None
            except:
                pass
        self.progress = -1

    def quit(self):
        self.stop()
