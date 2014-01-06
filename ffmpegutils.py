import subprocess


def get_mp3_encoder():
    encoder = None
    s = subprocess.Popen(['ffmpeg', '-codecs'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in s.stdout.readlines():
        if 'libmp3lame' in line:
            if line.replace(' ', '')[1] == 'E':
                encoder = 'libmp3lame'

    return encoder
