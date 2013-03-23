"""
Script to generate module file that describes available properties.

Since there is no way to get this table directly from mplayer, I am hard-coding
it from mplayer documentation.

If it changes, you can just pass the name of a text file containing the 
property table as an argument to this module:

$ python -m mpylayer.gen_properties prop.txt

and prop_table.py will be generated accordingly.

"""

text = """\
osdlevel           int       0       3       X   X   X    as -osdlevel
speed              float     0.01    100     X   X   X    as -speed
loop               int       -1              X   X   X    as -loop
filename           string                    X            file playing wo path
path               string                    X            file playing
demuxer            string                    X            demuxer used
stream_pos         pos       0               X   X        position in stream
stream_start       pos       0               X            start pos in stream
stream_end         pos       0               X            end pos in stream
stream_length      pos       0               X            (end - start)
chapter            int       0               X   X   X    select chapter
angle              int       0               X   X   X    select angle
length             time                      X            length of file in seconds
percent_pos        int       0       100     X   X   X    position in percent
time_pos           time      0               X   X   X    position in seconds
metadata           str list                  X            list of metadata key/value
metadata/*         string                    X            metadata values
volume             float     0       100     X   X   X    change volume
balance            float     -1      1       X   X   X    change audio balance
mute               flag      0       1       X   X   X
audio_delay        float     -100    100     X   X   X
audio_format       int                       X
audio_codec        string                    X
audio_bitrate      int                       X
samplerate         int                       X
channels           int                       X
switch_audio       int       -2      255     X   X   X    select audio stream
switch_angle       int       -2      255     X   X   X    select DVD angle
switch_title       int       -2      255     X   X   X    select DVD title
fullscreen         flag      0       1       X   X   X
deinterlace        flag      0       1       X   X   X
ontop              flag      0       1       X   X   X
rootwin            flag      0       1       X   X   X
border             flag      0       1       X   X   X
framedropping      int       0       2       X   X   X    1 = soft, 2 = hard
gamma              int       -100    100     X   X   X
brightness         int       -100    100     X   X   X
contrast           int       -100    100     X   X   X
saturation         int       -100    100     X   X   X
hue                int       -100    100     X   X   X
panscan            float     0       1       X   X   X
vsync              flag      0       1       X   X   X
video_format       int                       X
video_codec        string                    X
video_bitrate      int                       X
width              int                       X            "display" width
height             int                       X            "display" height
fps                float                     X
aspect             float                     X
switch_video       int       -2      255     X   X   X    select video stream
switch_program     int       -1      65535   X   X   X    (see TAB default keybind)
sub                int       -1              X   X   X    select subtitle stream
sub_source         int       -1      2       X   X   X    select subtitle source
sub_file           int       -1              X   X   X    select file subtitles
sub_vob            int       -1              X   X   X    select vobsubs
sub_demux          int       -1              X   X   X    select subs from demux
sub_delay          float                     X   X   X
sub_pos            int       0       100     X   X   X    subtitle position
sub_alignment      int       0       2       X   X   X    subtitle alignment
sub_visibility     flag      0       1       X   X   X    show/hide subtitles
sub_forced_only    flag      0       1       X   X   X
sub_scale          float     0       100     X   X   X    subtitles font size
tv_brightness      int       -100    100     X   X   X
tv_contrast        int       -100    100     X   X   X
tv_saturation      int       -100    100     X   X   X
tv_hue             int       -100    100     X   X   X
teletext_page      int       0       799     X   X   X
teletext_subpage   int       0       64      X   X   X
teletext_mode      flag      0       1       X   X   X    0 - off, 1 - on
teletext_format    int       0       3       X   X   X    0 - opaque,
                                                          1 - transparent,
                                                          2 - opaque inverted,
                                                          3 - transp. inv.
teletext_half_page int       0       2       X   X   X    0 - off, 1 - top half,
                                                          2- bottom half"""


def _int_zero(value):
    try:
        return float(value)
    except ValueError:
        return None


def _gen_property_table(_help_text):
    table = {}
    for line in _help_text:
        print line
        name = line[:19].strip()
        if '*' in name:
            continue
        if name:
            result = {
            'name': name,
            'type': line[19:29].strip(),
            'min': _int_zero(line[29:37].strip()),
            'max': _int_zero(line[37:45].strip()),
            'get': line[45:46] == 'X',
            'set': line[49:50] == 'X',
            'step': line[53:54] == 'X',
            'comment': line[58:].strip(),
            }
        else:
            name = result['name']
            result['comment'] += '\n' + line[58:].strip()
        table[name] = result
    return table

if __name__ == '__main__':
    from pprint import pformat
    from sys import argv
    if len(argv) > 1:
        text = open(argv[1])
    else:
        text = text.splitlines()
    
    f = open('prop_table.py', 'w')
    f.write('property_table = %s' % pformat(_gen_property_table(text), indent=4))
    f.close()
