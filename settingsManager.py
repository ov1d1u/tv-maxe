#-*- coding: utf-8 -*-
import ConfigParser, os, shutil, gtk, gobject, threading, json, random, tools
import which, subprocess
try:
    import remoteC
except:
    remoteC = None

slist = []
slist.append([1, 'http://tv-maxe.org/subscriptions/Romania.db'])
slist.append([1, 'http://tv-maxe.org/subscriptions/International'])


def migrateSettings():
    global slist
    print "Migrating settings..."
    cfgfile = os.getenv('HOME') + '/.tvmaxe'
    config = ConfigParser.ConfigParser()
    config.read(cfgfile)
    subs = config.get('General', 'subscriptions')
    for x in subs.split(';'):
        slist.append([1, x])
    config.set('General', 'subscriptions', json.dumps(slist))
    with open(cfgfile, 'wb') as configfile:
        config.write(configfile)
    shutil.move(os.getenv('HOME') + '/.tvmaxe', os.getenv('HOME') + '/.tvmaxe_')
    os.mkdir(os.getenv('HOME') + '/.tvmaxe')
    shutil.move(os.getenv('HOME') + '/.tvmaxe_', os.getenv('HOME') + '/.tvmaxe/config')


if not os.path.exists(os.getenv('HOME') + '/.tvmaxe'):
    os.mkdir(os.getenv('HOME') + '/.tvmaxe')
else:
    if not os.path.isdir(os.getenv('HOME') + '/.tvmaxe'):
        migrateSettings()

cfgfile = os.getenv('HOME') + '/.tvmaxe/config'
config = ConfigParser.ConfigParser()

class settingsManager:
    def __init__(self, parent):
        global slist
        self.slist = slist
        self.parent = parent
        self.cfgfile = cfgfile
        self.gui = self.parent.gui
        self.abonamente = self.getSubscriptions()
        self.updateList = False
        if not os.path.exists(cfgfile):
            config.add_section('General')
            config.set('General', 'volume', '1.0')
            try:
                import mpylayer
                mpylayer.MPlayerControl()
                config.set('General', 'backend', 'MPlayer')
            except:
                config.set('General', 'backend', 'GStreamer')
                try:
                    import vlc
                except:
                    config.set('General', 'internal', 'False')
            config.set('General', 'internal', 'True')
            config.set('General', 'player', '/usr/bin/totem')
            config.set('General', 'staticports', 'False')
            config.set('General', 'inport', '10320')
            config.set('General', 'outport', '10321')
            config.set('General', 'enableremote', 'True')
            config.set('General', 'enablehttpremote', 'False')
            config.set('General', 'remoteport', '8080')
            config.set('General', 'aspect', 'Auto')
            config.set('General', 'contrast', '1.0')
            config.set('General', 'brightness', '1.0')
            config.set('General', 'saturation', '1.0')
            config.set('General', 'showDonate', '')
            config.set('General', 'statusIcon', 'False')
            config.set('General', 'theme', self.getTheme())
            config.set('General', 'shutdownCMD', self.guess_shutdown_cmd())
            config.set('General', 'subscriptions', json.dumps(self.slist))
            config.set('General', 'windowSize', '660x437')
            config.set('General', 'HPanedPosition', '210')
            config.add_section('Remote')
            config.set('Remote', 'playpause', '00000000000100a4')
            config.set('Remote', 'switch_fullscreen', '0000000000010174')
            config.set('Remote', 'stop', '0000000000010080')
            config.set('Remote', 'volumeup', '0000000000010073')
            config.set('Remote', 'volumedown', '0000000000010072')
            config.set('Remote', 'mute', '0000000000010071')
            config.set('Remote', 'quit', '0000000000010179')
            config.set('Remote', 'nextchannel', '0000000000010192')
            config.set('Remote', 'prevchannel', '0000000000010193')
            config.set('Remote', 'info', '000000000001008b')
            config.set('Remote', 'up', '0000000000010067')
            config.set('Remote', 'down', '000000000001006c')
            config.set('Remote', 'ok', '0000000000010160')
            config.set('Remote', 'sleep', '000000000001008e')
            config.add_section('PBX')
            config.set('PBX', 'username', '')
            config.set('PBX', 'password', '')
            config.set('PBX', 'remember', 'False')
            config.add_section('Recording')
            config.set('Recording', 'recordingQuality', '5')
            config.set('Recording', 'acodec', 'copy')
            config.set('Recording', 'vcodec', 'copy')
            config.set('Recording', 'format', 'matroska')
            config.add_section('Petrodava')
            config.set('Petrodava', 'enable', 'False')
            config.set('Petrodava', 'server', 'petrodava.tv-maxe.org')
            config.set('Petrodava', 'port', '80')
            config.set('Petrodava', 'username', 'petrodava')
            config.set('Petrodava', 'password', 'petrodava')

            with open(cfgfile, 'wb') as configfile:
                config.write(configfile)

        self.petrodavaPortChanged_handler =\
            self.gui.get_object('petrodavaPort').connect('key-release-event', self.petrodavaPortChanged, None)
        self.petrodavaEnableChanged_handler =\
            self.gui.get_object('petrodavaEnable').connect('toggled', self.petrodavaEnableChanged, None)

        self.initiallabel53text = self.gui.get_object('label53').get_text()
        self.readSettings()
        self.setAbonamente()

    def showGUI(self, obj):
        self.updateWindow()
        self.gui.get_object('window2').show()

    def hideGUI(self, obj, event=None):
        self.gui.get_object('window2').hide()
        self.gui.get_object('petrodavaPort').disconnect(self.petrodavaPortChanged_handler)
        self.gui.get_object('petrodavaEnable').disconnect(self.petrodavaEnableChanged_handler)

        return True

    def toggleInternalPlayer(self, obj, event=None):
        self.gui.get_object('al_internal').set_sensitive(True)
        self.gui.get_object('al_external').set_sensitive(False)

    def toggleExternalPlayer(self, obj, event=None):
        self.gui.get_object('al_external').set_sensitive(True)
        self.gui.get_object('al_internal').set_sensitive(False)

    def toggleStaticPorts(self, obj, event=None):
        if obj.get_active():
            self.gui.get_object('alignment3').set_sensitive(True)
        else:
            self.gui.get_object('alignment3').set_sensitive(False)

    def toggleEnableRemote(self, obj, event=None):
        if obj.get_active():
            self.gui.get_object('alignment4').set_sensitive(True)
            if not hasattr(self.parent, 'infrared'):
                self.parent.infrared.initRemote()
        else:
            self.gui.get_object('alignment4').set_sensitive(False)
            self.parent.infrared.stopRemote()

    def toggleEnableHTTP(self, obj, event=None):
        if obj.get_active():
            self.gui.get_object('alignment6').set_sensitive(True)
        else:
            self.gui.get_object('alignment6').set_sensitive(False)
            self.parent.HTTPremote.stop()

    def toggleAbonament(self, obj, path):
        model = self.gui.get_object('liststore1')
        model[path][0] = not model[path][0]
        for x in self.abonamente:
            if model[path][1] == x[1]:
                if model[path][0]:
                    x[0] = 1
                else:
                    x[0] = 0
        self.updateList = True

    def petrodavaPortChanged(self, obj = None, *args):
        text = self.gui.get_object('petrodavaPort').get_text().strip()
        self.gui.get_object('petrodavaPort').set_text(
            ''.join([i for i in text if i in '0123456789'])
        )
        self.gui.get_object('label53').set_text(
            self.initiallabel53text.format(self.gui.get_object('petrodavaPort').get_text())
        )

    def petrodavaEnableChanged(self, obj = None, *args):
        self.gui.get_object('petrodavaSettings').set_sensitive(
            self.gui.get_object('petrodavaEnable').get_active()
        )

    def updateWindow(self):
        if self.internal is True:
            self.gui.get_object('radiobutton1').set_active(True)
        else:
            self.gui.get_object('radiobutton2').set_active(True)
        liststore = self.gui.get_object('liststore2')
        iter = liststore.get_iter_root()
        while (iter):
            if liststore.get_value(iter, 0).lower() == self.backend.lower():
                break
            iter = liststore.iter_next(iter)
        if iter:
            self.gui.get_object('combobox1').set_active_iter(iter)
        self.gui.get_object('entry1').set_text(self.getPlayer())
        self.gui.get_object('checkbutton1').set_active(self.staticports)
        self.gui.get_object('spinbutton1').set_value(float(self.inport))
        self.gui.get_object('spinbutton2').set_value(float(self.outport))
        self.gui.get_object('spinbutton3').set_value(float(self.remoteport))
        self.gui.get_object('checkbutton4').set_active(self.statusIcon)
        self.gui.get_object('shutdown_cmd').set_text(self.shutdowncmd)
        self.gui.get_object('recQuality_adjustment').set_value(self.recQuality)
        if which.which('irw'):
            self.gui.get_object('checkbutton2').set_active(self.enableremote)
        else:
            self.gui.get_object('checkbutton2').set_sensitive(False)
        self.gui.get_object('checkbutton5').set_active(self.enablehttpremote)
        self.gui.get_object('button6').set_label(self.remote_playpause)
        self.gui.get_object('button8').set_label(self.remote_switch_fullscreen)
        self.gui.get_object('button7').set_label(self.remote_stop)
        self.gui.get_object('button10').set_label(self.remote_volumeup)
        self.gui.get_object('button11').set_label(self.remote_volumedown)
        self.gui.get_object('button9').set_label(self.remote_mute)
        self.gui.get_object('button14').set_label(self.remote_quit)
        self.gui.get_object('button13').set_label(self.remote_nextchannel)
        self.gui.get_object('button12').set_label(self.remote_prevchannel)
        self.gui.get_object('button16').set_label(self.remote_info)
        self.gui.get_object('button21').set_label(self.remote_up)
        self.gui.get_object('button22').set_label(self.remote_down)
        self.gui.get_object('button23').set_label(self.remote_ok)
        self.gui.get_object('button54').set_label(self.remote_sleep)
        self.gui.get_object('petrodavaEnable').set_active(self.petrodavaEnable)
        self.gui.get_object('petrodavaServer').set_text(self.petrodavaServer)
        self.gui.get_object('petrodavaPort').set_text(self.petrodavaPort)
        self.gui.get_object('petrodavaUsername').set_text(self.petrodavaUsername)
        self.gui.get_object('petrodavaPassword').set_text(self.petrodavaPassword)

        self.petrodavaEnableChanged()
        self.petrodavaPortChanged()
        self.updateThemesList()
        self.updateRecordingsLists()

    def updateThemesList(self):
        self.gui.get_object('themestore').clear()
        cwd = os.getcwd() + '/'
        themesdir = [cwd + 'themes', os.getenv('HOME') + '/.tvmaxe/themes']
        selected = None
        for _dir in themesdir:
            if os.path.exists(_dir):
                for theme in os.listdir(_dir):
                    themepath = _dir + '/' + theme
                    if os.path.isdir(themepath):
                        if os.path.exists(themepath + '/theme'):
                            iter = self.gui.get_object('themestore').append([theme, themepath])
                            if os.path.relpath(self.getTheme(), themepath) == '.':
                                selected = iter
        if selected:
            self.gui.get_object('combobox_themes').set_active_iter(selected)

    def updateRecordingsLists(self):
        if not which.which('ffmpeg'):
            self.gui.get_object('acodec_combobox').set_sensitive(False)
            self.gui.get_object('vcodec_combobox').set_sensitive(False)
            return
        liststore = self.gui.get_object('acodec_liststore')
        liststore.clear()
        acodecs = self.getFFMPEG('acodecs')
        acodecs['copy'] = 'Copy'
        for key, value in sorted(acodecs.iteritems(), key=lambda (k, v): (v, k)):
            iter = liststore.append([key, value])
            if key == self.getACodec():
                self.gui.get_object('acodec_combobox').set_active_iter(iter)
        liststore = self.gui.get_object('vcodec_liststore')
        liststore.clear()
        vcodecs = self.getFFMPEG('vcodecs')
        vcodecs['copy'] = 'Copy'
        for key, value in sorted(vcodecs.iteritems(), key=lambda (k, v): (v, k)):
            iter = liststore.append([key, value])
            if key == self.getVCodec():
                self.gui.get_object('vcodec_combobox').set_active_iter(iter)
        liststore = self.gui.get_object('format_liststore')
        liststore.clear()
        formats = self.getFFMPEG('formats')
        for key, value in sorted(formats.iteritems(), key=lambda (k, v): (v, k)):
            iter = liststore.append([key, value])
            if key == self.getFormat():
                self.gui.get_object('format_combobox').set_active_iter(iter)

    def setAbonamente(self):
        model = self.gui.get_object('liststore1')
        model.clear()
        for x in self.abonamente:
            if x[0] == 1:
                model.append([True, x[1]])
            else:
                model.append([False, x[1]])

    def mapRemote(self, obj):
        self.gui.get_object('label23').set_text('0000000000000000')
        self.gui.get_object('window3').show()
        self.parent.infrared.infrared.callbacks.pop(self.parent.infrared.infrared.callbacks.index(self.parent.infrared.receiveIR))
        self.parent.infrared.infrared.callbacks.append([self.listenIR, [obj]])

    def listenIR(self, key, obj=None):
        self.gui.get_object('label23').set_text(key)
        gobject.timeout_add(1000, self.hideIR, None)
        obj.set_label(key)
        self.parent.infrared.infrared.callbacks.pop()
        self.parent.infrared.infrared.callbacks.append(self.parent.infrared.receiveIR)

    def hideIR(self, obj, event=None):
        self.gui.get_object('window3').hide()
        if event:
            return True
        else:
            return False

    def getFFMPEG(self, what):
        result = {}
        if not which.which('ffmpeg'):
            return None
        if what == 'acodecs' or what == 'vcodecs':
            exe = ['ffmpeg', '-codecs']
        elif what == 'formats':
            exe = ['ffmpeg', '-formats']
        ffmpeg = subprocess.Popen(exe, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        ffmpeg.wait()
        gotIt = False
        for x in ffmpeg.stdout.readlines():
            line = x[:-1]
            if not line.startswith(' '):
                continue
            if line[1] == '-':
                gotIt = True
                continue
            if not gotIt:
                continue
            caps = line[:6]
            codename = line[8:].split(' ', 1)[0]
            name = line[8:].split(' ', 1)[1]
            name = name[:75] + (name[75:] and '...')
            if what == 'acodecs':
                if caps[2:4] == 'EA':
                    result[codename] = name.lstrip()
            if what == 'vcodecs':
                if caps[2:4] == 'EV':
                    result[codename] = name.lstrip()
            caps = line[:3]
            codename = line[4:].split(' ', 1)[0]
            name = line[4:].split(' ', 1)[1]
            if what == 'formats':
                if caps[2] == 'E':
                    result[codename] = name.lstrip()
        return result

    def guess_shutdown_cmd(self):
        de = tools.guess_de()
        des = { 'xfce' : 'xfce4-session-logout --halt',
                'gnome' : 'gnome-session-save --shutdown-dialog',
                'ubuntu' : 'gnome-session-quit --power-off',
                'mate' : 'mate-session-save --shutdown-dialog',
                'kde' : 'qdbus org.kde.ksmserver /KSMServer logout 0 2 2',
                'cinnamon': 'cinnamon-session-quit --power-off --no-prompt'}
        if de and des.has_key(de):
            return des[de]
        else:
            return 'shutdown -h now'

    def Save(self, obj):
        if self.gui.get_object('spinbutton1').get_value() == self.gui.get_object('spinbutton2').get_value():
            dialog = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('Incoming and outgoing ports cannot be the same. Please review your settings.'));
            dialog.set_title(_('Configuration error'));
            dialog.run();
            dialog.destroy();
            return
        self.saveSettings()
        self.hideGUI(obj)


#####################################################################################
    def readSettings(self):
        config.read(cfgfile)
        self.volume = self.getVolume()
        self.backend = self.getBackend()
        self.player = self.getPlayer()
        self.internal = self.getInternal()
        self.shutdowncmd = self.getShutdown()
        self.recQuality = self.getRecQuality()
        self.staticports = self.getStaticPorts()
        self.enableremote = self.getRemote()
        self.enablehttpremote = self.getHTTPRemote()
        self.remoteport = self.getRemotePort()
        self.statusIcon = self.getStatusIcon()
        self.theme = self.getTheme()
        self.aspectratio = self.getAspect()
        self.inport = self.getInport()
        self.outport = self.getOutport()
        self.abonamente = self.getSubscriptions()
        self.petrodavaEnable = self.getEnablePetrodava()
        self.petrodavaServer = self.getPetrodavaServer()
        self.petrodavaPort = self.getPetrodavaPort()
        self.petrodavaUsername = self.getPetrodavaUsername()
        self.petrodavaPassword = self.getPetrodavaPassword()
        self.getRemoteButtons()

    def getRemoteButtons(self):
        try:
            self.remote_playpause = config.get('Remote', 'playpause')
        except:
            self.remote_playpause = '00000000000100a4'
        try:
            self.remote_switch_fullscreen = config.get('Remote', 'switch_fullscreen')
        except:
            self.remote_switch_fullscreen = '0000000000010174'
        try:
            self.remote_stop = config.get('Remote', 'stop')
        except:
            self.remote_stop = '0000000000010080'
        try:
            self.remote_volumeup = config.get('Remote', 'volumeup')
        except:
            self.remote_volumeup = '0000000000010073'
        try:
            self.remote_volumedown = config.get('Remote', 'volumedown')
        except:
            self.remote_volumedown = '0000000000010072'
        try:
            self.remote_mute = config.get('Remote', 'mute')
        except:
            self.remote_mute = '0000000000010071'
        try:
            self.remote_quit = config.get('Remote', 'quit')
        except:
            self.remote_quit = '0000000000010179'
        try:
            self.remote_nextchannel = config.get('Remote', 'nextchannel')
        except:
            self.remote_nextchannel = '0000000000010192'
        try:
            self.remote_prevchannel = config.get('Remote', 'prevchannel')
        except:
            self.remote_prevchannel = '0000000000010193'
        try:
            self.remote_info = config.get('Remote', 'info')
        except:
            self.remote_info = '000000000001008b'
        try:
            self.remote_up = config.get('Remote', 'up')
        except:
            self.remote_up = '0000000000010067'
        try:
            self.remote_down = config.get('Remote', 'down')
        except:
            self.remote_down = '000000000001006c'
        try:
            self.remote_ok = config.get('Remote', 'ok')
        except:
            self.remote_ok = '0000000000010160'
        try:
            self.remote_sleep = config.get('Remote', 'sleep')
        except:
            self.remote_sleep = '000000000001008e'

    def getInport(self):
        try:
            val = int(float(config.get('General', 'inport')))
        except:
            val = random.randint(10025, 65535)
        return val

    def getOutport(self):
        try:
            val = int(float(config.get('General', 'outport')))
        except Exception, e:
            val = random.randint(10025, 65535)
        return val

    def getStaticPorts(self):
        try:
            val = config.getboolean('General', 'staticports')
        except:
            val = False
        return val

    def getVideoEQ_channel(self, channelID):
        section_name = 'ChannelSettings_{0}'.format(channelID)
        if not config.has_section(section_name):
            return None
        val = {}
        try:
            val['b'] = config.getfloat(section_name, 'brightness')
        except:
            val['b'] = 0.0
        try:
            val['c'] = config.getfloat(section_name, 'contrast')
        except:
            val['c'] = 0.0
        try:
            val['s'] = config.getfloat(section_name, 'saturation')
        except:
            val['s'] = 0.0
        return val

    def getVideoEQ_global(self):
        val = {}
        try:
            val['b'] = config.getfloat('General', 'brightness')
        except:
            val['b'] = 0.0
        try:
            val['c'] = config.getfloat('General', 'contrast')
        except:
            val['c'] = 0.0
        try:
            val['s'] = config.getfloat('General', 'saturation')
        except:
            val['s'] = 0.0
        return val

    def getPBXuser(self):
        try:
            user = config.get('PBX', 'username')
        except:
            user = ''
        try:
            pasw = config.get('PBX', 'password')
        except:
            pasw = ''
        try:
            rem = config.getboolean('PBX', 'remember')
        except:
            rem = False
        return [rem, user, pasw]

    def getVolume(self):
        try:
            vol = config.getfloat('General', 'volume')
        except:
            vol = 1.0
        return vol

    def getBackend(self):
        try:
            backend = config.get('General', 'backend')
        except:
            backend = 'vlc'
        if backend == 'vlc':
            try:
                import vlc
            except:
                backend = 'mplayer'
        elif backend == 'mplayer':
            try:
                import mpylayer
                mpylayer.MPlayerControl
            except:
                backend = 'vlc'
        return backend

    def getInternal(self):
        try:
            internal = config.getboolean('General', 'internal')
        except:
            internal = True
        return internal

    def getPlayer(self):
        try:
            player = config.get('General', 'player')
        except:
            player = '/usr/bin/mplayer'
        return player

    def getRemote(self):
        try:
            val = config.getboolean('General', 'enableremote')
        except:
            val = False
        if which.which('irw'):
            return val
        else:
            return False

    def getHTTPRemote(self):
        try:
            val = config.getboolean('General', 'enablehttpremote')
        except:
            val = False
        return val

    def getRemotePort(self):
        try:
            val = config.get('General', 'remoteport')
        except:
            val = 8080
        return val

    def getAspect_channel(self, channelID):
        section_name = 'ChannelSettings_{0}'.format(channelID)
        if not config.has_section(section_name):
            return None
        try:
            aspect = config.get(section_name, 'aspect')
        except:
            aspect = 'Auto'
        return aspect


    def getAspect(self):
        try:
            aspect = config.get('General', 'aspect')
        except:
            aspect = 'Auto'
        return aspect

    def getDonate(self):
        try:
            donate = config.getfloat('General', 'showDonate')
        except:
            donate = '0.0'
        return donate

    def getShutdown(self):
        try:
            shutdown = config.get('General', 'shutdownCMD')
        except:
            shutdown = self.guess_shutdown_cmd()
        return shutdown

    def getRecQuality(self):
        try:
            quality = config.getfloat('Recording', 'recordingQuality')
        except Exception, e:
            quality = 5.0
        return quality

    def getACodec(self):
        try:
            acodec = config.get('Recording', 'acodec')
        except Exception, e:
            acodec = 'copy'
        return acodec

    def getVCodec(self):
        try:
            vcodec = config.get('Recording', 'vcodec')
        except Exception, e:
            vcodec = 'copy'
        return vcodec

    def getFormat(self):
        try:
            format = config.get('Recording', 'format')
        except Exception, e:
            format = 'avi'
        return format

    def getStatusIcon(self):
        try:
            status = config.getboolean('General', 'statusIcon')
        except:
            status = False
        return status

    def getTheme(self):
        try:
            theme = config.get('General', 'theme')
        except:
            theme = os.path.dirname(os.path.realpath(__file__)) + '/themes/default'
        return theme

    def getWindowSize(self):
        try:
            wsize = config.get('General', 'windowSize')
        except:
            wsize = '660x437'
        sizes = wsize.split('x')
        x = int(sizes[0])
        y = int(sizes[1])
        return [x, y]

    def getSubscriptions(self):
        try:
            subs = config.get('General', 'subscriptions')
        except:
            subs = json.dumps(self.slist)
        slist = json.loads(subs)
        return slist

    def getEnablePetrodava(self):
        try:
            enable = config.getboolean('Petrodava', 'enable')
        except:
            return False
        return enable

    def getPetrodavaServer(self):
        try:
            server = config.get('Petrodava', 'server')
        except:
            server = 'petrodava.tv-maxe.org'
        return server

    def getPetrodavaPort(self):
        try:
            port = config.get('Petrodava', 'port')
        except:
            port = '80'
        return port

    def getPetrodavaUsername(self):
        try:
            username = config.get('Petrodava', 'username')
        except:
            username = ''
        return username

    def getPetrodavaPassword(self):
        try:
            password = config.get('Petrodava', 'password')
        except:
            password = ''
        return password

    def getHPanedPosition(self):
        try:
            pos = config.get('General', 'HPanedPosition')
        except:
            pos = '210'
        return int(pos)

##################################################################

    def applySettings(self):
        if self.gui.get_object('radiobutton1').get_active():
            if self.backend.lower() != self.gui.get_object('combobox1').get_active_text().lower():
                if self.gui.get_object('combobox1').get_active_text().lower() == 'vlc-tvmx':
                    try:
                        import vlc
                        self.parent.mediaPlayer.quit()
                        self.backend = self.gui.get_object('combobox1').get_active_text().lower()
                        self.parent.stopCallback()
                    except:
                        self.backend = 'gstreamer'
                elif self.gui.get_object('combobox1').get_active_text().lower() == 'mplayer':
                    try:
                        import mpylayer
                        mpylayer.MPlayerControl()
                        self.parent.mediaPlayer.quit()
                        self.backend = self.gui.get_object('combobox1').get_active_text().lower()
                        self.parent.stopCallback()
                    except:
                        self.backend = 'gstreamer'
                elif self.gui.get_object('combobox1').get_active_text().lower() == 'gstreamer':
                    try:
                        import gst, pygst
                        self.parent.mediaPlayer.quit()
                        self.backend = self.gui.get_object('combobox1').get_active_text().lower()
                        self.parent.stopCallback()
                    except:
                        self.backend = 'mplayer'
                self.parent.mediaPlayer = self.parent.players[self.backend]

        if self.internal != self.gui.get_object('radiobutton1').get_active():
            self.internal = self.gui.get_object('radiobutton1').get_active()
            try:
                self.parent.mediaPlayer.stop()
            except:
                pass
            if self.gui.get_object('radiobutton1').get_active():
                self.gui.get_object('menuitem8').set_sensitive(True)
                self.gui.get_object('menuitem7').set_sensitive(True)
                self.gui.get_object('checkmenuitem1').set_sensitive(True)
                self.gui.get_object('vbox2').show()
            if self.gui.get_object('radiobutton2').get_active():
                self.gui.get_object('menuitem8').set_sensitive(False)
                self.gui.get_object('menuitem7').set_sensitive(False)
                self.gui.get_object('checkmenuitem1').set_sensitive(False)
                self.gui.get_object('vbox2').hide()
            self.gui.get_object('menuitem7').activate()

        if self.enableremote != self.gui.get_object('checkbutton2').get_active():
                if self.gui.get_object('checkbutton2').get_active():
                    pass#self.parent.initRemote()
                else:
                    self.parent.infrared.quit()

        if self.enablehttpremote != self.gui.get_object('checkbutton5').get_active():
                if self.gui.get_object('checkbutton5').get_active():
                    self.parent.HTTPremote.stop()
                    self.parent.HTTPremote.start(int(self.gui.get_object('spinbutton3').get_value()))
                else:
                    self.parent.HTTPremote.stop()

        if self.remoteport != self.gui.get_object('spinbutton3').get_value():
            self.parent.HTTPremote.stop()
            self.parent.HTTPremote.start(int(self.gui.get_object('spinbutton3').get_value()))

        if not self.internal:
            self.parent.radioWidget.modTV(None)
            self.parent.gui.get_object('modradiomenu').set_sensitive(False)
        self.parent.channelList(self.parent.gui.get_object('menuitem7'))

    def saveSettings(self):
        self.applySettings()
        if not config.has_section('General'):
            config.add_section('General')
        if not config.has_section('Remote'):
            config.add_section('Remote')
        if not config.has_section('Recording'):
            config.add_section('Recording')
        if not config.has_section('Petrodava'):
            config.add_section('Petrodava')
        config.set('General', 'backend', self.gui.get_object('combobox1').get_active_text())
        config.set('General', 'internal', self.gui.get_object('radiobutton1').get_active())
        config.set('General', 'player', self.gui.get_object('entry1').get_text())
        config.set('General', 'staticports', self.gui.get_object('checkbutton1').get_active())
        config.set('General', 'inport', self.gui.get_object('spinbutton1').get_value())
        config.set('General', 'outport', self.gui.get_object('spinbutton2').get_value())
        config.set('General', 'enableremote', self.gui.get_object('checkbutton2').get_active())
        config.set('General', 'enablehttpremote', self.gui.get_object('checkbutton5').get_active())
        config.set('General', 'remoteport', self.gui.get_object('spinbutton3').get_value())
        config.set('General', 'statusIcon', self.gui.get_object('checkbutton4').get_active())
        if self.gui.get_object('combobox_themes').get_active_iter():
            config.set('General', 'theme', self.gui.get_object('themestore')[self.gui.get_object('combobox_themes').get_active_iter()][1])
        config.set('General', 'shutdownCMD', self.gui.get_object('shutdown_cmd').get_text())
        config.set('General', 'subscriptions', json.dumps(self.abonamente))
        config.set('Remote', 'playpause', self.gui.get_object('button6').get_label())
        config.set('Remote', 'switch_fullscreen', self.gui.get_object('button8').get_label())
        config.set('Remote', 'stop', self.gui.get_object('button7').get_label())
        config.set('Remote', 'volumeup', self.gui.get_object('button10').get_label())
        config.set('Remote', 'volumedown', self.gui.get_object('button11').get_label())
        config.set('Remote', 'mute', self.gui.get_object('button9').get_label())
        config.set('Remote', 'quit', self.gui.get_object('button14').get_label())
        config.set('Remote', 'nextchannel', self.gui.get_object('button13').get_label())
        config.set('Remote', 'prevchannel', self.gui.get_object('button12').get_label())
        config.set('Remote', 'info', self.gui.get_object('button16').get_label())
        config.set('Remote', 'up', self.gui.get_object('button21').get_label())
        config.set('Remote', 'down', self.gui.get_object('button22').get_label())
        config.set('Remote', 'ok', self.gui.get_object('button23').get_label())
        config.set('Remote', 'sleep', self.gui.get_object('button54').get_label())
        config.set('Recording', 'recordingQuality', self.gui.get_object('recQuality_adjustment').get_value())
        if self.gui.get_object('acodec_combobox').get_active_iter():
            config.set('Recording', 'acodec', self.gui.get_object('acodec_liststore')[self.gui.get_object('acodec_combobox').get_active_iter()][0])
        if self.gui.get_object('vcodec_combobox').get_active_iter():
            config.set('Recording', 'vcodec', self.gui.get_object('vcodec_liststore')[self.gui.get_object('vcodec_combobox').get_active_iter()][0])
        if self.gui.get_object('format_combobox').get_active_iter():
            config.set('Recording', 'format', self.gui.get_object('format_liststore')[self.gui.get_object('format_combobox').get_active_iter()][0])
        config.set('Petrodava', 'enable', self.gui.get_object('petrodavaEnable').get_active())
        config.set('Petrodava', 'server', self.gui.get_object('petrodavaServer').get_text())
        config.set('Petrodava', 'port', self.gui.get_object('petrodavaPort').get_text())
        config.set('Petrodava', 'username', self.gui.get_object('petrodavaUsername').get_text())
        config.set('Petrodava', 'password', self.gui.get_object('petrodavaPassword').get_text())
        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()
        self.parent.readTheme()
        if self.updateList:
            self.parent.abonamente = self.abonamente
            self.parent.refreshList(None)
            self.updateList = False

    def saveVolume(self):
        if not config.has_section('General'):
            config.add_section('General')
        config.set('General', 'volume', self.gui.get_object('volumebutton1').get_value())

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveAspect_channel(self, aspect, channelID):
        section_name = 'ChannelSettings_{0}'.format(channelID)
        if not config.has_section(section_name):
            config.add_section(section_name)
        config.set(section_name, 'aspect', aspect)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveAspect_global(self, aspect):
        if not config.has_section('General'):
            config.add_section('General')
        config.set('General', 'aspect', aspect)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveVideoEQ_channel(self, b, c, s, channelID):
        section_name = 'ChannelSettings_{0}'.format(channelID)
        if not config.has_section(section_name):
            config.add_section(section_name)
        config.set(section_name, 'contrast', c)
        config.set(section_name, 'brightness', b)
        config.set(section_name, 'saturation', s)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveVideoEQ_global(self, b, c, s):
        if not config.has_section('General'):
            config.add_section('General')
        config.set('General', 'contrast', c)
        config.set('General', 'brightness', b)
        config.set('General', 'saturation', s)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def savePBX(self, rem, user, pasw):
        if not config.has_section('PBX'):
            config.add_section('PBX')

        config.set('PBX', 'remember', rem)
        config.set('PBX', 'username', user)
        config.set('PBX', 'password', pasw)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveDonate(self, version):
        config.set('General', 'showDonate', version)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveWindowSize(self, x, y):
        xsize = str(x)
        ysize = str(y)
        config.set('General', 'windowSize', xsize + 'x' + ysize)

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

    def saveHPanedPosition(self, pos):
        config.set('General', 'HPanedPosition', str(pos))

        with open(cfgfile, 'wb') as configfile:
            config.write(configfile)
        self.readSettings()

