#!/usr/bin/python
#-*- coding: utf-8 -*-

version = 0.09
basehost = 'http://www.tv-maxe.org/'

import gettext, locale, gtk.glade,  os
GETTEXT_DOMAIN = 'tvmaxe'
try:
    LOCALE_PATH = os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'lng')
except:
    LOCALE_PATH = 'lng'
locale.setlocale(locale.LC_ALL, '')
for module in gtk.glade, gettext:
    module.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
    module.textdomain(GETTEXT_DOMAIN)

def translate(text):
    try:
        #text = unicode(text, errors='ignore')
        return unicode(gettext.gettext(text), errors='ignore')
    except:
        return gettext.gettext(text)

import __builtin__
__builtin__._ = translate

import sys, tempfile
#os.chdir('/usr/share/tvmaxe')
import pygtk, gobject
pygtk.require('2.0')
import gtk
import subprocess, threading, urllib2, workerpool, random, time, datetime, webbrowser, string, copy
import irwatch, which, sqlite3, re, json, base64, StringIO
import tools, keysim, scheduler, socketserver
from PIL import Image
from settingsManager import settingsManager
from channel import Channel
from scheduler import Scheduler
from programTV import *
from tvmlist import ListParser
from pbx import PBX
from statusimage import StatusImage
from iconDownloader import IconDownloader
from radioWidget import RadioWidget
from blacklist import Blacklist
from autosleep import Sleep
from recorder import Recorder
from diagnostics import Diagnostics
import remoteC
gtk.gdk.threads_init()

tvmaxedir = os.getenv('HOME') + '/.tvmaxe/'

class TVMaxe:
    def __init__(self, autostart = None):
        self.gui = gtk.Builder()
        self.gui.add_from_file('tvmaxe.glade')
        self.settingsManager = settingsManager(self)
        self.autosleep = Sleep(self)
        self.channels = {}
        self.radioWidget = RadioWidget(self)
        self.HTTPremote = self.initHTTPRemote()
        self.gui.connect_signals({"on_imagemenuitem5_activate" : self.quit,
                                  "on_window1_delete_event" : self.quit,
                                  "listPress" : self.listPress,
                                  "radioListPress" : self.radioListPress,
                                  "fullscreen" : self.fullscreen,
                                  "playpause" : self.playpause,
                                  "stop" : self.stop,
                                  "hideCursor" : self.hideCursor,
                                  "setVolume" : self.setVolume,
                                  "mainWindowsKeyRelease" : self.mainWindowsKeyRelease,
                                  "show_settings" : self.settingsManager.showGUI,
                                  "hide_settings" : self.settingsManager.hideGUI,
                                  "save_settings" : self.settingsManager.Save,
                                  "toggleInternalPlayer" : self.settingsManager.toggleInternalPlayer,
                                  "toggleExternalPlayer" : self.settingsManager.toggleExternalPlayer,
                                  "toggleStaticPorts" : self.settingsManager.toggleStaticPorts,
                                  "toggleEnableRemote" : self.settingsManager.toggleEnableRemote,
                                  "toggleEnableHTTP" : self.settingsManager.toggleEnableHTTP,
                                  "toggleStatusIcon" : self.settingsManager.toggleStatusIcon,
                                  "mapRemote" : self.settingsManager.mapRemote,
                                  "hideIR" : self.settingsManager.hideIR,
                                  "toggleAbonament" : self.settingsManager.toggleAbonament,
                                  "channelList" : self.channelList,
                                  "showGhidTV" : self.showGhidTV,
                                  "hideGhidTV" : self.hideGhidTV,
                                  "pgDetails" : self.pgDetails,
                                  "updateEPG" : self.updateEPG,
                                  "drawLogo" : self.drawLogo,
                                  "showAbout" : self.showAbout,
                                  "hideAbout" : self.hideAbout,
                                  "mouseRemote" : self.mouseRemote,
                                  "ShowDetails" : self.ShowDetails,
                                  "hideShowDetails" : self.hideShowDetails,
                                  "refreshList" : self.refreshList,
                                  "showAddStream" : self.showAddStream,
                                  "hideAddStream" : self.hideAddStream,
                                  "tabSwitch" : self.tabSwitch,
                                  "addNewChannel" : self.addNewChannel,
                                  "deleteChannel" : self.deleteChannel,
                                  "showVideoEQ" : self.showVideoEQ,
                                  "applyVideoSettings" : self.applyVideoSettings,
                                  "videoEQreset" : self.videoEQreset,
                                  "hideVideoEQ" : self.hideVideoEQ,
                                  "saveVideoEQ_global" : self.saveVideoEQ_global,
                                  "saveVideoEQ_channel" : self.saveVideoEQ_channel,
                                  "loginPBX" : self.loginPBX,
                                  "hidePBX" : self.hidePBX,
                                  "connectPBX" : self.connectPBX,
                                  "donate" : self.donate,
                                  "donated" : self.donated,
                                  "adaugaAbonament" : self.adaugaAbonament,
                                  "hideAdaugaAbonament" : self.hideAdaugaAbonament,
                                  "addSubscription" : self.addSubscription,
                                  "editAbonament" : self.editAbonament,
                                  "hideEditAbonament" : self.hideEditAbonament,
                                  "stergeAbonament" : self.stergeAbonament,
                                  "saveEditAbonament" : self.saveEditAbonament,
                                  "hideShowTVMaxe" : self.hideShowTVMaxe,
                                  "hideShowTVMaxe_Menu" : self.hideShowTVMaxe_Menu,
                                  "channelInfo" : self.channelInfo,
                                  "hideChannelInfo" : self.hideChannelInfo,
                                  "channelInfo_raporteaza" : self.channelInfo_raporteaza,
                                  "statusIconVolume" : self.statusIconVolume,
                                  "modRadio" : self.radioWidget.modRadio,
                                  "modTV" : self.radioWidget.modTV,
                                  "prevChannel" : self.prevChannel,
                                  "nextChannel" : self.nextChannel,
                                  "hideError" : self.hideError,
                                  "blmanager" : self.blmanager,
                                  "hideblmanager" : self.hideblmanager,
                                  "removeBlacklisted" : self.removeBlacklisted,
                                  "blclear" : self.blclear,
                                  "refilter" : self.refilter,
                                  "addChanel_selectIcon" : self.addChanel_selectIcon,
                                  "browseSubscription" : self.browseSubscription,
                                  "saveChannellist" : self.saveChannellist,
                                  "showSleep" : self.autosleep.show,
                                  "hideSleep" : self.autosleep.hide,
                                  "okSleep" : self.autosleep.ok,
                                  "cancelShutdown" : self.autosleep.cancel,
                                  "readTheme" : self.readTheme,
                                  "showScheduler" : self.showScheduler,
                                  "tvguide_popmenu" : self.tvguide_popmenu,
                                  "hideScheduler" : self.hideScheduler,
                                  "addScheduler" : self.addScheduler,
                                  "showSchedMan" : self.showSchedMan,
                                  "hideSchedMan" : self.hideSchedMan,
                                  "removeSchedule" : self.removeSchedule,
                                  "editSchedule" : self.editSchedule,
                                  "record" : self.record,
                                  "showDiagnostics" : self.showDiagnostics,
                                  "closeDiagnostics" : self.closeDiagnostics,
                                  "runDiagnostics" : self.runDiagnostics,
                                  "diagnosticSelect" : self.diagnosticSelect
        })

        drawingarea = self.gui.get_object('drawingarea1')
        drawingarea.modify_bg(gtk.STATE_NORMAL, drawingarea.get_colormap().alloc_color("black"))
        self.gui.get_object('eventbox1').modify_bg(gtk.STATE_NORMAL, self.gui.get_object('eventbox1').get_colormap().alloc_color("black"))
        tools.label_set_autowrap(self.gui.get_object('label62'))
        tools.label_set_autowrap(self.gui.get_object('label29'))
        self.statusbar(_('Ready'))

        if not self.settingsManager.internal:
            self.gui.get_object('vbox2').hide()
            self.gui.get_object('checkmenuitem1').set_sensitive(False)
            self.gui.get_object('menuitem7').set_sensitive(False)

        self.accel_group = gtk.AccelGroup()
        self.gui.get_object('window1').add_accel_group(self.accel_group)
        self.gui.get_object('checkmenuitem1').add_accelerator("activate", self.accel_group, ord("F"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.gui.get_object('menuitem7').add_accelerator("activate", self.accel_group, ord("H"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.combobox2h = None
        self.combobox3h = None
        self.hideTimeout = None
        self.lastIter = None
        self.radioMode = False
        self.tvmaxevis = True
        self.progressbarPulse = None
        self.getTime_to = None
        self.autostart = autostart
        self.urlIndex = 0
        self.sLock = False
        self.currentChannel = None
        self.recordingMode = False
        self.abonamente = self.settingsManager.getSubscriptions()
        wsize = self.settingsManager.getWindowSize()
        self.gui.get_object('window1').resize(wsize[0], wsize[1])
        hpaned = self.settingsManager.getHPanedPosition()
        self.gui.get_object('hpaned1').set_position(hpaned)
        self.gui.get_object('statusicon1').set_visible(self.settingsManager.getStatusIcon())

        if autostart:
            self.logo = [0, ['Please wait,', 'your channel will be played immediately']]
        else:
            self.logo = [0, 'TV-MAXE ' + str(version)]
        if not which.which('ffmpeg'):
            self.gui.get_object('button61').hide()
            self.gui.get_object('menuitem47').hide()

        self.gui.get_object('window1').show()
        self.channelsort = gtk.TreeModelSort(self.gui.get_object('channelstore'))
        self.channelsort.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self.radiosort = gtk.TreeModelSort(self.gui.get_object('radiostore'))
        self.radiosort.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self.channelfilter = self.channelsort.filter_new()
        self.channelfilter.set_visible_func(self.sortme)
        self.radiofilter = self.radiosort.filter_new()
        self.radiofilter.set_visible_func(self.sortme)
        self.gui.get_object('treeview1').set_model(self.channelfilter)
        self.gui.get_object('treeview3').set_model(self.radiofilter)
        self.gui.get_object('liststatuslabel').set_text(_("Total: %s channels in %s subscriptions" % ('0', str(len(self.settingsManager.getSubscriptions())))))
        self.gui.get_object('aboutdialog1').set_version(str(version))
        self.gui.get_object('recqScale').set_show_fill_level(False)
        self.gui.get_object('recqScale').add_mark(1, gtk.POS_LEFT, 'Very high')
        self.gui.get_object('recqScale').add_mark(8, gtk.POS_LEFT, 'High')
        self.gui.get_object('recqScale').add_mark(16, gtk.POS_LEFT, 'Normal')
        self.gui.get_object('recqScale').add_mark(24, gtk.POS_LEFT, 'Low')
        self.gui.get_object('recqScale').add_mark(35, gtk.POS_LEFT, 'Very low')

        self.tvguide = ProgramTV()
        self.keysimulator = keysim.KeySim()
        self.pbx = PBX()
        self.showDonate()
        self.setupProtocols()
        self.setupPlayers()
        self.blacklist = Blacklist()
        self.StatusImage = StatusImage()
        self.Scheduler = Scheduler(os.path.abspath(__file__), self)
        self.readTheme()
        self.buildComboDays()
        self.SocketServer = socketserver.SocketServer(self)
        self.infrared = irwatch.Main({
                "playpause" : self.playpause,
                "fullscreen" : self.fullscreen,
                "stop" : self.stop,
                "setVolume" : self.setVolume,
                "mute" : self.mute,
                "quit" : self.quit,
                "nextChannel" : self.nextChannel,
                "prevChannel" : self.prevChannel,
                "showEPG" : self.showEPG,
                "remoteUP" : self.remoteUP,
                "remoteDOWN" : self.remoteDOWN,
                "remoteOK" : self.remoteOK,
                "remoteSLEEP" : self.autosleep.remote
                })
        threading.Thread(target=self.getChannels, args=(self.populateList,)).start()
        self.initPlayer()
        gobject.timeout_add(500, self.drawLogo)

    def setupProtocols(self):
        self.protocols = {}
        protocols_dir = os.getcwd() + '/protocols/'
        sys.path.append(protocols_dir)
        files = os.listdir(protocols_dir)
        for x in files:
            p = protocols_dir + x
            if not os.path.isdir(p):
                if x.endswith('.py'):
                    x = os.path.splitext(x)
                    x = x[0]
                    try:
                        loadmod = __import__(x)
                        self.protocols[x] = loadmod.Protocol(self.play, self.stop)
                    except Exception, e:
                        print e
                        pass

    def setupPlayers(self):
        self.players = {}
        liststore = self.gui.get_object('liststore2')
        drawable = self.gui.get_object('drawingarea1')
        if drawable.window:
            xid = drawable.window.xid
        else:
            xid = None
        players_dir = os.getcwd() + '/players/'
        sys.path.append(players_dir)
        files = os.listdir(players_dir)
        for x in files:
            modul = players_dir + x
            if not os.path.isdir(modul):
                if x.endswith('.py'):
                    x = os.path.splitext(x)
                    x = x[0]
                    try:
                        loadmod = __import__(x)
                        self.players[x] = loadmod.Player(self.playCallback, xid)
                        if self.players[x].name != 'External':
                            liststore.append([self.players[x].name])
                    except Exception, e:
                        print e

        backend = self.settingsManager.backend
        if self.settingsManager.internal:
            try:
                self.mediaPlayer = self.players[backend.lower()]
            except Exception, e:
                self.mediaPlayer = self.players['mplayer']
        else:
            loadmod = __import__('external')
            self.mediaPlayer = loadmod.Player(self.playCallback, self.settingsManager.player)
        self.Recorder = Recorder(self.playCallback, xid, copy.copy(self.mediaPlayer), self.settingsManager)
        self.applyVideoSettings()

    def initPlayer(self):
        self.isFullscreen = False
        self.paused = False
        self.cursorTimeout = None

        if self.settingsManager.enableremote:
            self.infrared.initRemote(self.settingsManager)
        if self.settingsManager.enablehttpremote:
            self.HTTPremote.start(int(float(self.settingsManager.remoteport)))
        self.gui.get_object('volumebutton1').set_value(self.settingsManager.volume)
        self.gui.get_object('volumebutton2').set_value(self.settingsManager.volume)
        self.applyVideoSettings()

    def drawLogo(self, obj=None, event=None):
        if hasattr(self, 'mediaPlayer'):
            if self.mediaPlayer.mprunning:
                return True
        drawingarea = self.gui.get_object('drawingarea1')
        if drawingarea.window:
            text = self.logo[1]
            if self.logo[0] == 0:
                self.StatusImage.draw(drawingarea, text, 'logo')
            if self.logo[0] == 1:
                self.StatusImage.draw(drawingarea, text, 'loading')
            if self.logo[0] == 2:
                self.StatusImage.draw(drawingarea, text, 'error')
        return True

    def getChannels(self, callback):
        try:
            pbxlogin = self.settingsManager.getPBXuser()
            if pbxlogin[0]:
                self.pbx.working = False
                gobject.idle_add(self.loginPBX, None, True)
        except Exception, e:
            print e
        callback(None)                  # load user's channel list
        for x in self.abonamente:
            if x[0] == 0:
                continue
            if x[1].startswith('file://'):
                if os.path.exists(x[1][7:]):
                    fh = open(x[1][7:], 'r')
                    data = fh.read()
                    fh.close()
                    gobject.idle_add(callback, data, x[1])
                    return
            if x[1].startswith('http://'):
                savefile = x[1].replace("http://", "")
                savefile = re.sub(r'\W+', '', savefile)
                savefile = tvmaxedir + 'cache/' + savefile
                try:
                    if os.path.exists(savefile):
                        fh = open(savefile, "rb")
                        data = fh.read()
                        fh.close()
                        gobject.idle_add(callback, data, x[1])
                    if not os.path.exists(tvmaxedir + 'cache/'):
                        os.mkdir(tvmaxedir + 'cache/')
                    req = urllib2.Request(x[1])
                    response = urllib2.urlopen(req)
                    data = response.read()
                    fh = open(savefile, "wb")
                    fh.write(data)
                    fh.close()
                    gobject.idle_add(callback, data, x[1])
                except Exception, e:
                    print e
                    gobject.idle_add(self.listError)
        gobject.idle_add(self.autoplay)
        gobject.timeout_add(2000, self.createTrayMenus)

    def populateList(self, data, abo = None):
        channelstore = self.gui.get_object('channelstore')
        radiostore = self.gui.get_object('radiostore')
        if not data:
            dbfile = os.getenv('HOME') + '/.tvmaxe/userlist.db'
            if not os.path.exists(dbfile):
                return
            userlist = open(dbfile, 'rb')
            data = userlist.read()
            userlist.close()
            self.parseList(data, channelstore, radiostore)
            return
        if '|newchannel|' in data:
            self.parseOldList(data, abo)
        else:
            channelstore = self.gui.get_object('channelstore')
            radiostore = self.gui.get_object('radiostore')
            self.parseList(data, channelstore, radiostore)

    def addChannel(self, channel, liststore, idleadd=False):
        id = channel.id
        image = channel.icon
        name = channel.name
        url = channel.streamurls[:]
        iter = None
        if type(url) == list:
            for x in url:
                if not self.protocolCheck(x):
                    channel.streamurls.pop(channel.streamurls.index(x))
            if len(channel.streamurls) == 0:
                return
        else:
            if not self.protocolCheck(url):
                return
        self.channels[id] = channel
        if id in self.channels:                                 # canalul exista deja in baza de date, il actualizam...
            iter = self.channels[id].get_iter()
            if iter:                                            # canalul exista si in lista din GUI, actualizam intrarea...
                liststore.set_value(iter, 1, image)
                liststore.set_value(iter, 2, name)
            else:                                               # canalul exista in baza de date, dar nu si in GUI (probabil a fost sters?)
                if not self.blacklist.is_blacklisted(channel):
                    iter = liststore.append([id, image, name])  # il adaugam in GUI...
                    if channel.guide != '':
                        self.gui.get_object('tvguidestore').append([id, image, name])
        else:
            if not self.blacklist.is_blacklisted(channel):
                iter = liststore.append([id, image, name])
                if channel.guide != '':
                    self.gui.get_object('tvguidestore').append([id, image, name])
        self.gui.get_object('liststatuslabel').set_text(_("Total: %s channels in %s subscriptions" % (str(self.countChannels()), str(len(self.settingsManager.abonamente)))))
        if idleadd:
            return False
        return iter

    def parseList(self, data, channelstore, radiostore):
        tmp = tempfile.mktemp()
        fh = open(tmp, 'wb')
        fh.write(data)
        fh.close()
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        conn.text_factory = str
        data = conn.cursor()
        db_info = data.execute("SELECT * FROM info").fetchone()
        abo = db_info['name']
        gobject.idle_add(self.addabo, abo)
        rows = data.execute("SELECT * FROM tv_channels")
        for x in rows:
            url = json.loads(x['streamurls'])
            id = x['id']
            imgdata = base64.b64decode(x['icon'])
            buff = StringIO.StringIO(imgdata)
            im = Image.open(buff)
            image = tools.Image_to_GdkPixbuf(im)
            buff.close()
            name = x['name']
            params = json.loads(x['params'])
            tvguide = x['guide']
            audiochs = json.loads(x['audiochannels'])
            channel = Channel(id = id, icon = image, name = name, streamurls = url, params = params, guide = tvguide, audiochannels = audiochs, liststore = channelstore, source = abo)
            channel.info = db_info
            gobject.idle_add(self.addChannel, channel, channelstore, True)

        rows = data.execute("SELECT * FROM radio_channels")
        for x in rows:
            url = json.loads(x['streamurls'])
            id = x['id']
            imgdata = base64.b64decode(x['icon'])
            buff = StringIO.StringIO(imgdata)
            im = Image.open(buff)
            image = tools.Image_to_GdkPixbuf(im)
            buff.close()
            name = x['name']
            url = json.loads(x['streamurls'])
            params = json.loads(x['params'])
            channel = Channel(id = id, icon = image, name = name, streamurls = url, params = params, liststore = radiostore, source = abo)
            channel.info = db_info
            gobject.idle_add(self.addChannel, channel, radiostore, True)

    def parseOldList(self, data, abo):                      # abo ajuta la creearea id-ului unic al canalului
        gobject.idle_add(self.addabo, os.path.basename(abo))
        self.pool = workerpool.WorkerPool(size=10)
        if '|tvchannels|' in data:
            gtvch = data.split('|tvchannels|')
            gtvch = gtvch[1].split('|endoftvchannels|')
            channels = gtvch[0]
            channels = channels.split('|newchannel|')
            channels.pop(0)
            channelstore = self.gui.get_object('channelstore')
            for x in channels:
                cdata = x.split('|-|')
                nume = cdata[0]
                url = cdata[1]
                icon = cdata[2]
                if len(cdata) > 3:
                    chid = cdata[3]
                else:
                    chid = ''
                image = gtk.gdk.pixbuf_new_from_file('blank.gif')
                id = re.sub(r'\W+', '', abo + nume)
                channel = Channel(id = id, icon = image, name = nume, streamurls = [url], guide = chid, liststore = channelstore, source = os.path.basename(abo))
                channel.info = {'name' : os.path.basename(abo), 'version' : '0.01', 'author' : '', 'url' : 'http://www.pymaxe.com', 'epgurl' : ''}
                iter = self.addChannel(channel, channelstore)
                if iter:
                    threading.Thread(target=self.updateIcon, args=(channel, icon)).start()

        if '|radiochannels|' in data:
            grch = data.split('|radiochannels|')
            grch = grch[1].split('|endofradiochannels|')
            channels = grch[0]
            channels = channels.split('|newchannel|')
            channels.pop(0)
            channelstore = self.gui.get_object('radiostore')
            for x in channels:
                cdata = x.split('|-|')
                nume = cdata[0]
                url = cdata[1]
                icon = cdata[2]
                image = gtk.gdk.pixbuf_new_from_file('blank.gif')
                id = re.sub(r'\W+', '', abo + nume)
                channel = Channel(id = id, icon = image, name = nume, streamurls = [url], liststore = channelstore, source = os.path.basename(abo))
                channel.info = {'name' : os.path.basename(abo), 'version' : '0.01', 'author' : '', 'url' : 'http://www.pymaxe.com', 'epgurl' : ''}
                iter = self.addChannel(channel, channelstore)
                if iter:
                    threading.Thread(target=self.updateIcon, args=(channel, icon)).start()

    def updateIcon(self, channel, icon):
        job = IconDownloader(basehost, channel, icon, self.setIcon)
        self.pool.put(job)

    def setIcon(self, channel, imgdata):
        loader = gtk.gdk.PixbufLoader()
        loader.write(imgdata)
        loader.close()
        channel.icon = loader.get_pixbuf()
        channelstore = channel.liststore
        iter = channel.get_iter()
        channelstore.set_value(iter, 1, loader.get_pixbuf())

    def protocolCheck(self, url):
        toReturn = False
        for x in self.protocols:
            for y in self.protocols[x].protocols:
                if url.startswith(y):
                    toReturn = True
        return toReturn

    def getProtocol(self, url):
        if self.settingsManager.getEnablePetrodava():
          return self.protocols['Petrodava']

        for x in self.protocols:
            for y in self.protocols[x].protocols:
                if url.startswith(y):
                    return self.protocols[x]
        return None

    def generateStreamsMenu(self, id, mode, urls):
        if mode == 'tv':
            func = self.playChannel
        elif mode == 'radio':
            func = self.playRadioChannel
        elif mode == 'tv_rec':
            func = self.recordChannel
        elif mode == 'radio_rec':
            func = self.recordRadioChannel
        submenu = gtk.Menu()
        index = 0
        for url in urls:
            menu = gtk.MenuItem(url)
            menu.connect('activate', lambda obj, x = index: func(self.channels[id], x))
            menu.show()
            submenu.append(menu)
            index += 1
        return submenu

    def listPress(self, obj, event):
        self.gui.get_object('treeview3').get_selection().unselect_all()
        if hasattr(event, 'button'):
            self.gui.get_object('vbox18').hide()
            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                chList = self.gui.get_object('treeview1')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                self.urlIndex = 0
                channel = self.channels[model.get_value(iter, 0)]
                threading.Thread(target=self.playChannel, args=(channel,)).start()
                self.gui.get_object('modradiomenu').set_sensitive(False)
            if event.button == 3:
                x = int(event.x)
                y = int(event.y)
                pthinfo = obj.get_path_at_pos(x, y)
                if pthinfo is not None:
                    path, col, cellx, celly = pthinfo
                    obj.grab_focus()
                    obj.set_cursor( path, col, 0)
                    treeselection = obj.get_selection()
                    (model, iter) = treeselection.get_selected()
                    if iter:
                        id = model.get_value(iter, 0)
                        urls = self.channels[id].streamurls
                        chid = self.channels[id].guide
                        if chid != '':
                            if self.channels[id].info['epgurl'] != '':
                                self.gui.get_object('menuitem6').set_sensitive(True)
                        else:
                            self.gui.get_object('menuitem6').set_sensitive(False)
                        if len(urls) > 1:
                            submenu = self.generateStreamsMenu(id, 'tv', urls)
                            self.gui.get_object('menuitem40').set_submenu(submenu)
                            self.gui.get_object('menuitem40').show()
                            submenu = self.generateStreamsMenu(id, 'tv_rec', urls)
                            if hasattr(self, 'handler_menuitem47'):
                                self.gui.get_object('menuitem47').disconnect(self.handler_menuitem47)
                            self.gui.get_object('menuitem47').set_submenu(submenu)
                        else:
                            self.gui.get_object('menuitem40').hide()
                            self.gui.get_object('menuitem47').set_label('Record')
                            self.gui.get_object('menuitem47').set_submenu(None)
                            if hasattr(self, 'handler_menuitem47'):
                                self.gui.get_object('menuitem47').disconnect(self.handler_menuitem47)
                            self.handler_menuitem47 = self.gui.get_object('menuitem47').connect('activate', lambda obj: self.recordChannel(None))
                        self.gui.get_object('menu4').popup(None, None, None, event.button, event.time)
        elif hasattr(event, 'keyval'):
            if event.keyval == 65293:
                chList = self.gui.get_object('treeview1')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                self.urlIndex = 0
                channel = self.channels[model.get_value(iter, 0)]
                threading.Thread(target=self.playChannel, args=(channel,)).start()

    def radioListPress(self, obj, event):
        self.gui.get_object('treeview1').get_selection().unselect_all()
        if hasattr(event, 'button'):
            self.gui.get_object('vbox18').hide()
            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                chList = self.gui.get_object('treeview3')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                self.urlIndex = 0
                threading.Thread(target=self.playRadioChannel, args=(channel,)).start()
            if event.button == 3:
                x = int(event.x)
                y = int(event.y)
                pthinfo = obj.get_path_at_pos(x, y)
                if pthinfo is not None:
                    path, col, cellx, celly = pthinfo
                    obj.grab_focus()
                    obj.set_cursor( path, col, 0)
                    treeselection = obj.get_selection()
                    (model, iter) = treeselection.get_selected()
                    if iter:
                        id = model.get_value(iter, 0)
                        urls = self.channels[id].streamurls
                        chid = self.channels[id].guide
                        self.gui.get_object('menuitem6').set_sensitive(False)
                        if len(urls) > 1:
                            submenu = self.generateStreamsMenu(id, 'radio', urls)
                            self.gui.get_object('menuitem40').set_submenu(submenu)
                            self.gui.get_object('menuitem40').show()
                            if hasattr(self, 'handler_menuitem47'):
                                self.gui.get_object('menuitem47').disconnect(self.handler_menuitem47)
                                del self.handler_menuitem47
                            self.gui.get_object('menuitem47').set_label('Record stream')
                            submenu = self.generateStreamsMenu(id, 'radio_rec', urls)
                            if hasattr(self, 'handler_menuitem47'):
                                self.gui.get_object('menuitem47').disconnect(self.handler_menuitem47)
                            self.gui.get_object('menuitem47').set_submenu(submenu)
                        else:
                            self.gui.get_object('menuitem40').hide()
                            self.gui.get_object('menuitem47').set_label('Record')
                            self.gui.get_object('menuitem47').set_submenu(None)
                            if hasattr(self, 'handler_menuitem47'):
                                self.gui.get_object('menuitem47').disconnect(self.handler_menuitem47)
                            self.handler_menuitem47 = self.gui.get_object('menuitem47').connect('activate', lambda obj: self.recordRadioChannel(None))
                        self.gui.get_object('menu4').popup(None, None, None, event.button, event.time)
        elif hasattr(event, 'keyval'):
            if event.keyval == 65293:
                chList = self.gui.get_object('treeview3')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                self.urlIndex = 0
                threading.Thread(target=self.playRadioChannel, args=(channel,)).start()

    def playChannel(self, channel, index = None):
        self.stop(None)
        self.recordingMode = False
        self.currentChannel = channel
        index = index if index else self.urlIndex
        self.url = channel.streamurls[index]
        if self.url != '':
            if self.getTime_to:
                gobject.source_remove(self.getTime_to)
            self.logo = [1, _("Loading: %s" % self.currentChannel.name)]
            if self.urlIndex > 0:
                gobject.idle_add(self.statusbar, _('(Retrying) Loading ') + self.currentChannel.name)
                self.logo = [1, _('(Retrying) Loading: ') + self.currentChannel.name]
            else:
                gobject.idle_add(self.statusbar, _('Loading ') + self.currentChannel.name)
            gobject.idle_add(self.modradiomenuStatus, 'tv')
            protocol = self.getProtocol(self.url)
            protocol.inport, protocol.outport = self.protocolPorts()
            protocol.petrodava_server = self.settingsManager.getPetrodavaServer()
            protocol.petrodava_port = self.settingsManager.getPetrodavaPort()
            protocol.play(self.url, channel.params)
            if self.progressbarPulse:
                gobject.source_remove(self.progressbarPulse)
                self.progressbarPulse = None
            self.progressbarPulse = gobject.timeout_add(400, self.updateProgressbar, protocol)
        self.applyVideoSettings()

    def playRadioChannel(self, channel, index = None):
        self.stop(None)
        self.recordingMode = False
        self.currentChannel = channel
        index = index if index else self.urlIndex
        self.url = channel.streamurls[index]
        icon = channel.icon
        if self.url != '':
            if self.getTime_to:
                gobject.source_remove(self.getTime_to)
            if self.urlIndex > 0:
                gobject.idle_add(self.statusbar, _('(Retrying) Loading ') + self.currentChannel.name)
                self.logo = [1, _('(Retrying) Loading: ') + self.currentChannel.name]
            else:
                gobject.idle_add(self.statusbar, _('Loading ') + self.currentChannel.name)
            gobject.idle_add(self.radioWidget.updateWidget, self.currentChannel.name, self.url, icon)
            gobject.idle_add(self.modradiomenuStatus, 'radio')
            if self.url.endswith('.pls') or self.url.endswith('.m3u'):
                self.url = ListParser().getData(self.url)
            protocol = self.getProtocol(self.url)
            protocol.inport, protocol.outport = self.protocolPorts()
            protocol.play(self.url, channel.params)
            if self.progressbarPulse:
                gobject.source_remove(self.progressbarPulse)
                self.progressbarPulse = None
            self.progressbarPulse = gobject.timeout_add(400, self.updateProgressbar, protocol)

    def playURL(self, url):
        self.stop(None)
        self.recordingMode = False
        time.sleep(1)
        if not '://' in url:                 # making a base check if the protocol has been specified
            self.url = 'http://' + url   # we suppose that the user wants to play a HTTP stream...
        else:
            self.url = url
        # Try to find if the address already exists in list
        select = None
        if not select:
            model = self.channelfilter
            iter = model.get_iter_root()
            while iter:
                id = model.get_value(iter, 0)
                my_url = self.channels[id].streamurls
                if url in my_url:
                    self.currentChannel = self.channels[id]
                    chList = self.gui.get_object('treeview1')
                    treeselection = chList.get_selection()
                    treeselection.select_iter(iter)
                    select = 'tv'
                    break
                iter = model.iter_next(iter)
        if not select:
            model = self.radiofilter
            iter = model.get_iter_root()
            while iter:
                id = model.get_value(iter, 0)
                my_url = self.channels[id].streamurls
                if url in my_url:
                    self.currentChannel = self.channels[id]
                    chList = self.gui.get_object('treeview3')
                    treeselection = chList.get_selection()
                    treeselection.select_iter(iter)
                    select = 'radio'
                    break
                iter = model.iter_next(iter)
        if self.getTime_to:
            gobject.source_remove(self.getTime_to)
        if select == 'tv':
            chList = self.gui.get_object('treeview1')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
            self.urlIndex = 0
            self.playChannel(channel)
        elif select == 'radio':
            chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
            self.urlIndex = 0
            self.playRadioChannel(channel)
        else:
            if self.url != '':
                self.logo = [1, _("Loading: %s" % self.currentChannel.name)]
                gobject.idle_add(self.statusbar, _('Loading ') + self.currentChannel.name)
                gobject.idle_add(self.modradiomenuStatus, 'tv')
                protocol = self.getProtocol(self.url)
                protocol.inport, protocol.outport = self.protocolPorts()
                protocol.play(self.url)
                if self.progressbarPulse:
                    gobject.source_remove(self.progressbarPulse)
                    self.progressbarPulse = None
                self.progressbarPulse = gobject.timeout_add(400, self.updateProgressbar, protocol)

    def recordChannel(self, channel, index = None, askSave = True):
        self.stop(None)
        if askSave:
            self.Recorder.saveAs = self.saveRecord('video')
        if not self.Recorder.saveAs:
            return
        self.recordingMode = True
        if not channel:
            chList = self.gui.get_object('treeview1')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
        self.currentChannel = channel
        index = index if index else self.urlIndex
        self.url = channel.streamurls[index]
        if self.url != '':
            if self.getTime_to:
                gobject.source_remove(self.getTime_to)
            self.logo = [1, _("Recording: %s" % self.currentChannel.name)]
            if self.urlIndex > 0:
                gobject.idle_add(self.statusbar, _('(Retrying) Recording ') + self.currentChannel.name)
                self.logo = [1, _('(Retrying) Recording: ') + self.currentChannel.name]
            else:
                gobject.idle_add(self.statusbar, _('Recording ') + self.currentChannel.name)
            gobject.idle_add(self.modradiomenuStatus, 'tv')
            protocol = self.getProtocol(self.url)
            protocol.inport, protocol.outport = self.protocolPorts()
            protocol.play(self.url, channel.params)
            if self.progressbarPulse:
                gobject.source_remove(self.progressbarPulse)
                self.progressbarPulse = None
            self.progressbarPulse = gobject.timeout_add(400, self.updateProgressbar, protocol)

    def recordRadioChannel(self, channel, index = None, askSave = True):
        self.stop(None)
        if askSave:
            self.Recorder.saveAs = self.saveRecord('audio')
        if not self.Recorder.saveAs:
            return
        self.recordingMode = True
        if not channel:
            chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
        self.currentChannel = channel
        index = index if index else self.urlIndex
        self.url = channel.streamurls[index]
        icon = channel.icon
        if self.url != '':
            if self.getTime_to:
                gobject.source_remove(self.getTime_to)
            self.logo = [1, _("Recording: %s" % self.currentChannel.name)]
            if self.urlIndex > 0:
                gobject.idle_add(self.statusbar, _('(Retrying) Recording ') + self.currentChannel.name)
                self.logo = [1, _('(Retrying) Recording: ') + self.currentChannel.name]
            else:
                gobject.idle_add(self.statusbar, _('Recording ') + self.currentChannel.name)
            gobject.idle_add(self.radioWidget.updateWidget, self.currentChannel.name, self.url, icon)
            gobject.idle_add(self.modradiomenuStatus, 'radio')
            if self.url.endswith('.pls') or self.url.endswith('.m3u'):
                self.url = ListParser().getData(self.url)
            protocol = self.getProtocol(self.url)
            protocol.inport, protocol.outport = self.protocolPorts()
            protocol.play(self.url, channel.params)
            if self.progressbarPulse:
                gobject.source_remove(self.progressbarPulse)
                self.progressbarPulse = None
            self.progressbarPulse = gobject.timeout_add(400, self.updateProgressbar, protocol)

    def play(self, url):
        if self.recordingMode:
            if not hasattr(self.mediaPlayer, 'recQuality'):
                self.orig_mediaPlayer = copy.copy(self.mediaPlayer)
            del self.mediaPlayer
            self.mediaPlayer = copy.copy(self.Recorder)
        else:
            if hasattr(self, 'orig_mediaPlayer'):
                self.mediaPlayer = copy.copy(self.orig_mediaPlayer)
                del self.orig_mediaPlayer
        self.mediaPlayer.play(url)

    def modradiomenuStatus(self, t):
        if t == 'tv':
            self.gui.get_object('modradiomenu').set_sensitive(False)
        elif t == 'radio':
            if self.settingsManager.getInternal():
                self.gui.get_object('modradiomenu').set_sensitive(True)

    def stop(self, error=None):
        if type(error) == str:
            for x in self.protocols:
                self.protocols[x].stop()
            self.playerError(self.currentChannel)
            return
        if hasattr(self, 'url'):
            protocol = self.getProtocol(self.url)
            protocol.stop()
        else:
            for x in self.protocols:
                self.protocols[x].stop()
        self.isUpdatingProgressbar = False
        if type(error) == int:
            self.stopCallback(error)
        else:
            self.currentChannel = None
            self.stopCallback()

    def playCallback(self):
        if self.currentChannel:
            self.gui.get_object('label65').set_text(_("Playing: ") + self.currentChannel.name)
            self.gui.get_object('label80').set_text(_("Playing: ") + self.currentChannel.name)
            self.statusbar(_('Playing ') + self.currentChannel.name)
            if len(self.currentChannel.audiochannels) > 1:
                menu = gtk.Menu()
                for x in self.currentChannel.audiochannels:
                    item = gtk.MenuItem(x[1])
                    item.show()
                    item.connect("activate", self.changeAudioTrack, x[0])
                    menu.append(item)
                self.gui.get_object('menuitem43').set_submenu(menu)
                self.gui.get_object('menuitem43').show()
            else:
                self.gui.get_object('menuitem43').remove_submenu()
                self.gui.get_object('menuitem43').hide()
        self.gui.get_object('image1').set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.keysimulator.src = gobject.timeout_add(60000, self.keysimulator.start)
        self.mediaPlayer.volume(self.gui.get_object('volumebutton1').get_value())
        gobject.timeout_add(2000, self.showEPG)
        gobject.timeout_add(2000, self.applyVideoSettings, None)
        if hasattr(self, 'blinkRecord_source'):
            gobject.source_remove(self.blinkRecord_source)
            del self.blinkRecord_source
        self.blinkRecord_source = gobject.timeout_add(1000, self.blinkRecord)
        if self.getTime_to:
            gobject.source_remove(self.getTime_to)
        self.getTime_to = gobject.timeout_add(1000, self.getTime)
        try:
            drawingarea = self.gui.get_object('drawingarea1')
            gobject.timeout_add(200, drawingarea.modify_bg, gtk.STATE_NORMAL, drawingarea.get_colormap().alloc_color("black"))
        except:
            pass
        protocol = self.getProtocol(self.url)
        protocol.progress = -1
        return False

    def stopCallback(self, errorlevel = 0):
        if self.getTime_to:
            gobject.source_remove(self.getTime_to)
        self.recordingMode = False
        if errorlevel != 1:                                             # errorlevel == 1 means 'retry channel'
            threading.Thread(target=self.mediaPlayer.stop, args=()).start()
            if errorlevel == 0:                                     # errorlevel 0 means that the channel wasn't stopped because of an error
                self.logo = [0, 'TV-MAXE ' + str(version)]
            if hasattr(self.mediaPlayer, 'recQuality'):             # if we just recorded smth, trim the recording to match the recorded length
                recordedTime = self.gui.get_object('label36').get_label()
                l = recordedTime.split(':')
                seconds = int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])
                if seconds:
                    self.mediaPlayer.adjustTime(seconds)
            self.gui.get_object('image1').set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
            gobject.source_remove(self.keysimulator.src)
            self.gui.get_object('menuitem43').hide()
            gobject.idle_add(self.statusbar, _('Stopped'))
            self.gui.get_object('label36').set_text('00:00:00')
            self.gui.get_object('label83').set_text('00:00:00')

    def getTime(self):
        if not self.paused:
            if self.mediaPlayer.getStatus() == False:
                self.playerError(self.currentChannel)
                return False
            current = time.strftime('%H:%M:%S', time.gmtime(self.mediaPlayer.getTime()[0]))
            gobject.idle_add(self.gui.get_object('label36').set_text, str(current))
            gobject.idle_add(self.gui.get_object('label83').set_text, str(current))
        return True

    def fullscreen(self, obj, event=None):
        if event:
            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                self.switch_fullscreen(obj)
            elif event.button == 3:
                self.gui.get_object('menu5').popup(None, None, None, event.button, event.time)
                if self.mediaPlayer.isPlaying():
                    self.gui.get_object('menuitem_videoSettings').set_sensitive(True)
                else:
                    self.gui.get_object('menuitem_videoSettings').set_sensitive(False)
            elif event.button == 2:
                self.remoteOK()

        else:
            self.switch_fullscreen(obj)

    def switch_fullscreen(self, obj):
        if self.radioMode:
            return
        if not self.settingsManager.getInternal():
            return
        if not self.isFullscreen:
            self.gui.get_object('checkmenuitem1').set_active(True)
            self.gui.get_object('menuitem9').set_active(True)
            self.gui.get_object('menubar1').hide()
            #self.gui.get_object('notebook2').hide()
            self.gui.get_object('hbox1').hide()
            self.gui.get_object('vbox27').hide()
            self.gui.get_object('hbox32').hide()
            self.gui.get_object('hseparator1').hide()
            self.gui.get_object('window1').fullscreen()
            self.cursorTimeout = gobject.timeout_add(2000, self.hide, obj)
            self.isFullscreen = True
        else:
            self.gui.get_object('checkmenuitem1').set_active(False)
            self.gui.get_object('menuitem9').set_active(False)
            self.gui.get_object('window1').unfullscreen()
            self.gui.get_object('window1').show_all()
            self.channelList(self.gui.get_object('menuitem7'))
            self.gui.get_object('progressbar2').hide()
            self.gui.get_object('recordbox').hide()
            self.gui.get_object('vbox18').hide()
            self.isFullscreen = False

    def channelList(self, obj):
        if self.gui.get_object('radiobutton1').get_active():
            if obj.get_active():
                self.gui.get_object('vbox27').show()
            else:
                self.gui.get_object('vbox27').hide()
        else:
            self.gui.get_object('notebook2').show()

    def hideCursor(self, obj, event):
        if self.cursorTimeout:
            gobject.source_remove(self.cursorTimeout)
        self.gui.get_object('eventbox1').window.set_cursor(None)
        self.cursorTimeout = gobject.timeout_add(2000, self.hide, obj)

    def hide(self, obj):
        pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
        color = gtk.gdk.Color()
        invisible = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
        self.gui.get_object('eventbox1').window.set_cursor(invisible)
        return False

    def playpause(self, obj):
        if self.mediaPlayer.isPlaying() and obj == self.gui.get_object('button1'):
            self.mediaPlayer.pause()
            if not self.paused:
                self.gui.get_object('image1').set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
                self.paused = True
            else:
                self.gui.get_object('image1').set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
                self.paused = False
        else:
            page = self.gui.get_object('notebook2').get_current_page()
            if page == 0:
                chList = self.gui.get_object('treeview1')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                if iter:
                    channel = self.channels[model.get_value(iter, 0)]
                    self.urlIndex = 0
                    self.playChannel(channel)
                else:
                    model = chList.get_model()
                    iter = model.get_iter_root()
                    treeselection = chList.get_selection()
                    treeselection.select_iter(iter)
                    (model, iter) = treeselection.get_selected()
                    channel = self.channels[model.get_value(iter, 0)]
                    self.urlIndex = 0
                    self.playChannel(channel)
            elif page == 1:
                chList = self.gui.get_object('treeview3')
                treeselection = chList.get_selection()
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                if iter:
                    self.urlIndex = 0
                    self.playRadioChannel(channel)
                else:
                    model = chList.get_model()
                    iter = model.get_iter_root()
                    treeselection = chList.get_selection()
                    treeselection.select_iter(iter)
                    (model, iter) = treeselection.get_selected()
                    channel = self.channels[model.get_value(iter, 0)]
                    self.urlIndex = 0
                    self.playRadioChannel(channel)

    def record(self, obj):
        if self.mediaPlayer.isPlaying() and obj == self.gui.get_object('button1'):
            self.mediaPlayer.stop()
            self.gui.get_object('image1').set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
            if iter:
                self.urlIndex = 0
                self.recordChannel(channel)
            else:
                model = chList.get_model()
                iter = model.get_iter_root()
                treeselection = chList.get_selection()
                treeselection.select_iter(iter)
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                self.urlIndex = 0
                self.recordChannel(channel)
        elif page == 1:
            chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
            if iter:
                self.urlIndex = 0
                self.recordRadioChannel(channel)
            else:
                model = chList.get_model()
                iter = model.get_iter_root()
                treeselection = chList.get_selection()
                treeselection.select_iter(iter)
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                self.urlIndex = 0
                self.recordRadioChannel(channel)

    def setVolume(self, obj, value, step=0):
        if step == 0:
            self.mediaPlayer.volume(value)
            self.gui.get_object('volumebutton1').set_value(value)
            self.gui.get_object('volumebutton2').set_value(value)
        else:
            value = self.gui.get_object('volumebutton1').get_value() + step
            if value > 100.0:
                value = 100.0
            if value < 0.0:
                value = 0.0
            self.mediaPlayer.volume(value)
            self.gui.get_object('volumebutton1').set_value(value)
            self.gui.get_object('volumebutton2').set_value(value)

    def nextChannel(self, obj=None):
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            newiter = model.iter_next(iter)
        else:
            newiter = model.get_iter_root()
        if newiter:
            treeselection.select_iter(newiter)
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
        else:
            iter = model.get_iter_root()
            treeselection.select_iter(iter)
            (model, iter) = treeselection.get_selected()
            channel = self.channels[model.get_value(iter, 0)]
        if page == 0:
            self.urlIndex = 0
            self.playChannel(channel)
        elif page == 1:
            self.urlIndex = 0
            self.playRadioChannel(channel)

    def prevChannel(self, obj=None):
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            path = model.get_path(iter)
            row = path[0]
            if row > 0:
                prev_row = row - 1
                prev_iter = model.get_iter(prev_row)
                treeselection.select_iter(prev_iter)
                (model, iter) = treeselection.get_selected()
                channel = self.channels[model.get_value(iter, 0)]
                if page == 0:
                    self.urlIndex = 0
                    self.playChannel(channel)
                elif page == 1:
                    self.urlIndex = 0
                    self.playRadioChannel(channel)
            else:
                iter = model.get_iter_root()
                while iter:
                    lastIter = iter
                    iter = model.iter_next(iter)
                treeselection.select_iter(lastIter)
                selected = treeselection.get_selected()


    def mute(self):
        if self.gui.get_object('volumebutton1').get_value() != 0:
            self.lastVolume = self.gui.get_object('volumebutton1').get_value()
            self.mediaPlayer.volume(0)
            self.gui.get_object('volumebutton1').set_value(0)
            self.gui.get_object('volumebutton2').set_value(0)
        else:
            self.mediaPlayer.volume(self.lastVolume)
            self.gui.get_object('volumebutton1').set_value(self.lastVolume)
            self.gui.get_object('volumebutton2').set_value(self.lastVolume)

    def showEPG(self):
        try:
            self.tvguide.getCurrent(self.currentChannel, self.displayEPG)
        except:
            pass

    def displayEPG(self, nowontv, chName):
        if not chName == self.currentChannel.name:
            return
        if len(self.currentChannel.audiochannels) > 1:
            langMsg = _('Languages: %s' % (self.currentChannel.audiochannels[0][1]))
        else:
            langMsg = ''
        now = datetime.datetime.now()
        ceas = now.strftime("%H:%M")
        if nowontv:
            if langMsg != '':
                self.OSD('[' + ceas + ']' + nowontv + '\n' + self.currentChannel.name + '\n' + langMsg)
            else:
                self.OSD('[' + ceas + ']' + nowontv + '\n' + self.currentChannel.name)
        else:
            if langMsg != '':
                self.OSD('[' + ceas + ']' + '\n' + self.currentChannel.name + '\n' + langMsg)
            else:
                self.OSD('[' + ceas + ']' + '\n' + self.currentChannel.name)
        return False

    def OSD(self, text):
        self.mediaPlayer.OSD(text)

    def statusbar(self, message, percent=None):
        self.gui.get_object('label65').set_text(message)
        self.gui.get_object('label80').set_text(message)
        self.gui.get_object('statusicon1').set_tooltip_text(message)
        if percent:
            try:
                if percent == -1:
                    self.gui.get_object('progressbar2').hide()
                else:
                    r = float(percent)/float(100)
                    self.gui.get_object('progressbar2').set_fraction(r)
                    self.gui.get_object('progressbar2').show()
                if r >= 1.0:
                    gobject.timeout_add(1000, self.resetStatusbar)
            except:
                self.gui.get_object('progressbar2').set_fraction(0.0)

    def updateProgressbar(self, protocol):
        if protocol == None:
            self.gui.get_object('progressbar2').hide()
            return False
        percent = protocol.progress
        if percent == -1:
            self.gui.get_object('progressbar2').hide()
            return False
        if percent == 0:
            self.gui.get_object('progressbar2').pulse()
            self.gui.get_object('progressbar2').show()
            return True
        r = float(percent)/float(100)
        self.gui.get_object('progressbar2').set_fraction(r)
        self.gui.get_object('progressbar2').show()
        return True

    def resetStatusbar(self):
        self.gui.get_object('label65').set_text('')
        self.gui.get_object('label80').set_text('')
        self.gui.get_object('progressbar2').set_fraction(0)
        self.gui.get_object('progressbar2').hide()
        return False

    def mainWindowsKeyRelease(self, obj, event):
        if self.isFullscreen and event.keyval == 65307:
            self.switch_fullscreen(obj)
        if event.keyval == 109:
            self.mute()
        if self.isFullscreen and event.keyval == 65362:
            self.remoteUP()
        if self.isFullscreen and event.keyval == 65364:
            self.remoteDOWN()
        if self.isFullscreen and event.keyval == 65293:
            self.remoteOK()
        if self.isFullscreen and event.keyval == 65481:
            self.showEPG()

    def mouseRemote(self, obj, event):
        if event.direction.value_name == 'GDK_SCROLL_DOWN':
            self.remoteDOWN()
        elif event.direction.value_name == 'GDK_SCROLL_UP':
            self.remoteUP()

    def gtkMessage(self, tip, butoane, titlu, text):
        gtk.gdk.threads_enter()
        dialog = gtk.MessageDialog(parent=self.gui.get_object('window1'), flags=0, type=tip, buttons=butoane, message_format=text);
        dialog.set_title(titlu);
        resp = dialog.run();
        dialog.destroy();
        gtk.gdk.threads_leave();
        return False

    def showError(self, msg):
        self.gui.get_object('label31').set_text(msg)
        self.gui.get_object('window5').show()
        self.countdown = 5
        gobject.timeout_add(1000, self.error_countdown)

    def playerError(self, channel):
        if not channel:
            self.urlIndex = 0
            self.logo = [2, [_('NO SIGNAL'),
                            '',
                            '',
                            _('This channel seems to be offline.'),
                            _('Also, it could be unreachable because of'),
                            _('your network settings or restrictions.'),
                            '',
                            _('Please try again later')]
            ]
            self.stopCallback(2)
            return
        urls = channel.streamurls
        self.urlIndex += 1
        if self.urlIndex < len(channel.streamurls):
            # Try to find if the address already exists in list
            select = None
            if not select:
                model = self.gui.get_object('channelstore')
                iter = model.get_iter_root()
                while iter:
                    id = model.get_value(iter, 0)
                    if id in channel.id:
                        self.currentChannel = self.channels[id]
                        chList = self.gui.get_object('treeview1')
                        treeselection = chList.get_selection()
                        treeselection.select_iter(iter)
                        select = 'tv'
                        break
                    iter = model.iter_next(iter)
            if not select:
                model = self.gui.get_object('radiostore')
                iter = model.get_iter_root()
                while iter:
                    id = model.get_value(iter, 0)
                    if id in channel.id:
                        self.currentChannel = self.channels[id]
                        chList = self.gui.get_object('treeview3')
                        treeselection = chList.get_selection()
                        treeselection.select_iter(iter)
                        select = 'radio'
                        break
                    iter = model.iter_next(iter)
            if select == 'tv':
                chList = self.gui.get_object('treeview1')
                channel = self.currentChannel
                channel.streamurls[self.urlIndex]
                if self.recordingMode:
                    gobject.idle_add(self.recordChannel, channel, None, False)
                else:
                    gobject.idle_add(self.playChannel, channel)
            elif select == 'radio':
                chList = self.gui.get_object('treeview3')
                channel = self.currentChannel
                channel.streamurls[self.urlIndex]
                if self.recordingMode:
                    gobject.idle_add(self.recordRadioChannel, channel, None, False)
                else:
                    gobject.idle_add(self.playRadioChannel, channel)
            self.stop(1)
        else:
            self.urlIndex = 0
            self.logo = [2, [_('NO SIGNAL'),
                            '',
                            '',
                            _('This channel seems to be offline.'),
                            _('Also, it could be unreachable because of'),
                            _('your network settings or restrictions.'),
                            '',
                            _('Please try again later')]
            ]
            self.stopCallback(2)

    def retryPlay(self, func, channel):             # reincearca redarea
        func(channel)
        return False

    def error_countdown(self):
        if self.countdown != 0:
            self.countdown = self.countdown - 1
            self.gui.get_object('label32').set_text('Closing in %s seconds...' % str(self.countdown))
            return True
        else:
            self.hideError()
            return False

    def hideError(self, obj=None):
        self.gui.get_object('window5').hide()
        self.gui.get_object('label32').set_text('Closing in 5 seconds...')

    def showGhidTV(self, obj, channel=None):
        try:
            self.gui.get_object('combobox2').disconnect(self.combobox2h)
            self.gui.get_object('combobox3').disconnect(self.combobox3h)
        except:
            pass
        self.gui.get_object('scrolledwindow4').hide()
        self.gui.get_object('liststore4').clear()
        self.gui.get_object('image5').clear()
        treeselection = self.gui.get_object('treeview1').get_selection()
        (model, iter) = self.iterConvert(treeselection.get_selected())
        iter = tools.search_iter(self.gui.get_object('tvguidestore'), 0, model[iter][0])
        self.gui.get_object('combobox2').set_active_iter(iter)
        timp = self.gui.get_object('liststore3').get_value(self.gui.get_object('combobox3').get_active_iter(), 1)
        if not channel:
            id = self.gui.get_object('tvguidestore').get_value(self.gui.get_object('combobox2').get_active_iter(), 0)
            channel = self.channels[id]
        threading.Thread(target=self.tvguide.getGuideData, args=(timp, channel, self.fillGhidTV)).start()
        self.gui.get_object('window4').show()
        self.gui.get_object('window4').present()
        self.combobox2h = self.gui.get_object('combobox2').connect('changed', self.updateEPG)
        self.combobox3h = self.gui.get_object('combobox3').connect('changed', self.updateEPG)

    def fillGhidTV(self, data, chname=None, day=None):
        model = self.gui.get_object('liststore4')
        timp = self.gui.get_object('liststore3').get_value(self.gui.get_object('combobox3').get_active_iter(), 1)
        if day != timp:
            return
        id = self.gui.get_object('tvguidestore').get_value(self.gui.get_object('combobox2').get_active_iter(), 0)
        channel = self.channels[id]
        if chname != channel.name:
            return
        style = self.gui.get_object('treeview2').get_style()
        treeselection = self.gui.get_object('treeview2').get_selection()
        if data:
            ore = []
            for x in data:
                ore.append(x[0])
            ore.sort()
            H = str(time.strftime("%H", time.localtime()))
            M = int(time.strftime("%M", time.localtime()))
            if M != 59:
                M = str(M+1)
            else:
                M = str(M)
            if len(M) == 1:
                M = '0' + M
            acum = datetime.datetime.strptime(H+':'+M , "%H:%M")
            apro = [x for x in itertools.takewhile( lambda t: acum > datetime.datetime.strptime(t, "%H:%M"), ore )][-1]
            for x in data:
                ora = x[0]
                nume = x[1]
                link = x[2]
                if x[0] == apro:
                    color = style.bg[0]
                else:
                    color = style.base[0]
                iter = model.append([ora, nume, link, color])
                if x[0] == apro:
                    treeselection.select_iter(iter)
                    path = model.get_path(iter)
        self.gui.get_object('treeview2').scroll_to_cell(path)
        self.gui.get_object('treeview2').grab_focus()

    def pgDetails(self, obj, event=None):
        self.gui.get_object('image5').clear()
        self.gui.get_object('scrolledwindow4').hide()
        treeselection = self.gui.get_object('treeview2').get_selection()
        (model, iter) = treeselection.get_selected()
        url = model.get_value(iter, 2)
        threading.Thread(target=self.tvguide.getPgDetails, args=(url, self.showpgDetails)).start()

    def showpgDetails(self, data, data_url):
        treeselection = self.gui.get_object('treeview2').get_selection()
        (model, iter) = treeselection.get_selected()
        url = model.get_value(iter, 2)
        if url != data_url:
            return
        if data:
            self.gui.get_object('label30').set_text(data[1])
            self.gui.get_object('label29').set_text(data[2])
            if data[0]:
                loader = gtk.gdk.PixbufLoader()
                loader.write(data[0])
                loader.close()
                self.gui.get_object('image5').set_from_pixbuf(loader.get_pixbuf())
            self.gui.get_object('scrolledwindow4').show()
        else:
            self.gui.get_object('scrolledwindow4').hide()

    def hideGhidTV(self, obj, event=None):
        self.gui.get_object('window4').hide()
        return True

    def updateEPG(self, obj=None):
        try:
            self.gui.get_object('scrolledwindow4').hide()
            self.gui.get_object('liststore4').clear()
            self.gui.get_object('image5').clear()
            timp = self.gui.get_object('liststore3').get_value(self.gui.get_object('combobox3').get_active_iter(), 1)
            id = self.gui.get_object('tvguidestore').get_value(self.gui.get_object('combobox2').get_active_iter(), 0)
            threading.Thread(target=self.tvguide.getGuideData, args=(timp, self.channels[id], self.fillGhidTV)).start()
        except Exception, e:
            pass

    def remoteUP(self):
        if self.hideTimeout:
            gobject.source_remove(self.hideTimeout)
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        elif page == 2:
            return
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            path = model.get_path(iter)
            row = list(path)
            newlast = row[len(row)-1]-1
            if newlast < 0:
                row.pop()
            else:
                row[len(row)-1] = newlast
            row = tuple(row)
            if len(row) != 0:
                if row > 0:
                    prev_row = row
                    if prev_row > 0:
                        prev_iter = model.get_iter(prev_row)
                        treeselection.select_iter(prev_iter)
                        selected = treeselection.get_selected()
        else:
            iter = model.get_iter_root()
            if iter:
                treeselection.select_iter(iter)
            else:
                return
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        id = model[iter][0]
        channel = self.channels[id]
        self.gui.get_object('image9').set_from_pixbuf(channel.icon)
        self.gui.get_object('label39').set_text(channel.name)
        self.gui.get_object('label40').set_text(_("Press OK or middle-click to play this channel"))
        self.gui.get_object('label63').set_text('')
        self.gui.get_object('minutesLeft_pb').hide()
        try:
            if 'epgurl' in dict(channel.info):
                if channel.info['epgurl'] != '':
                    self.tvguide.getCurrent(channel, self.label63)
        except:
            pass
        if self.autosleep.timer:
            self.gui.get_object('sleepLabel').set_text(str(self.autosleep.get_minutes_left()) + ' minute(s)')
            self.gui.get_object('sleepBox').show()
        else:
            self.gui.get_object('sleepBox').hide()
        self.gui.get_object('vbox18').show()
        self.hideTimeout = gobject.timeout_add(4000, self.hidev18)

    def remoteDOWN(self):
        if self.hideTimeout:
            gobject.source_remove(self.hideTimeout)
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        elif page == 2:
            return
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        if not iter:
            iter = model.get_iter_root()
        name = model.get_value(iter, 1)
        if iter:
            name = model.get_value(iter, 1)
            newiter = model.iter_next(iter)
            if newiter:
                treeselection.select_iter(newiter)
                selected = treeselection.get_selected()
        else:
            iter = model.get_iter_root()
            if iter:
                treeselection.select_iter(iter)
            else:
                return
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
        elif page == 1:
            chList = self.gui.get_object('treeview3')
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        id = model[iter][0]
        channel = self.channels[id]
        self.gui.get_object('image9').set_from_pixbuf(channel.icon)
        self.gui.get_object('label39').set_text(channel.name)
        self.gui.get_object('label40').set_text(_("Press OK or middle-click to play this channel"))
        self.gui.get_object('label63').set_text('')
        self.gui.get_object('minutesLeft_pb').hide()
        try:
            if 'epgurl' in dict(channel.info):
                if channel.info['epgurl'] != '':
                    self.tvguide.getCurrent(channel, self.label63)
        except Exception, e:
            pass
        if self.autosleep.timer:
            self.gui.get_object('sleepLabel').set_text(str(self.autosleep.get_minutes_left()) + ' minute(s)')
            self.gui.get_object('sleepBox').show()
        else:
            self.gui.get_object('sleepBox').hide()
        self.gui.get_object('vbox18').show()
        self.hideTimeout = gobject.timeout_add(4000, self.hidev18)

    def label63(self, data, channelName):
        if data:
            page = self.gui.get_object('notebook2').get_current_page()
            if page == 0:
                chList = self.gui.get_object('treeview1')
            elif page == 1:
                chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            (model, iter) = treeselection.get_selected()
            id = model[iter][0]
            channel = self.channels[id]
            try:
                if channel.name == channelName:
                    self.gui.get_object('label63').set_text(data)
                    left = self.tvguide.minutesLeft(channel)
                    if left[0] != -1:
                        self.gui.get_object('minutesLeft_pb').set_text(_("%s left...") % str(left[0]))
                        self.gui.get_object('minutesLeft_pb').set_fraction(left[1])
                        self.gui.get_object('minutesLeft_pb').show()
                    else:
                        self.gui.get_object('minutesLeft_pb').hide()
            except:
                pass

    def remoteOK(self):
        chList = self.gui.get_object('treeview1')
        treeselection = chList.get_selection()
        (model, iter) = treeselection.get_selected()
        id = model[iter][0]
        channel = self.channels[id]
        if iter:
            if channel.name == model.get_value(iter, 1):
                self.hidev18()
                return
        if not self.gui.get_object('vbox18').props.visible:
            self.hidev18()
            return
        self.hidev18()
        self.urlIndex = 0
        self.playChannel(channel)

    def hidev18(self, iter=None):
        self.gui.get_object('vbox18').hide()
        if iter:
            pass
        return False

    def ShowDetails(self, obj, event=None):
        treeselection = self.gui.get_object('treeview4').get_selection()
        (model, iter) = treeselection.get_selected()
        description = model.get_value(iter, 2);
        photo = model.get_value(iter, 3);
        name = model.get_value(iter, 0);
        self.gui.get_object('label45').set_text(name)
        self.gui.get_object('label46').set_text(description)
        threading.Thread(target=self.downloadShowImage, args=(photo, )).start()
        self.gui.get_object('window6').set_title('Detalii: ' + name)
        self.gui.get_object('image10').hide()
        self.gui.get_object('window6').show()

    def downloadShowImage(self, url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        imgdata = response.read()
        gobject.idle_add(self.loadImage_n_ShowDetails, imgdata)

    def loadImage_n_ShowDetails(self, imgdata):
        loader = gtk.gdk.PixbufLoader()
        loader.write(imgdata)
        loader.close()
        self.gui.get_object('image10').set_from_pixbuf(loader.get_pixbuf())
        self.gui.get_object('image10').show()

    def hideShowDetails(self, obj, event=None):
        self.gui.get_object('window6').hide()
        return True

    def showAbout(self, obj):
        self.gui.get_object('aboutdialog1').show()

    def hideAbout(self, obj, event=None):
        self.gui.get_object('aboutdialog1').hide()
        return True

    def tabSwitch(self, obj, pointer, page):
        self.gui.get_object('imagemenuitem1').show()
        if page == 0: #la selectarea primului tab
            self.gui.get_object('imagemenuitem1').set_label(_('Add a TV channel'))
        if page == 1: #la selectarea celui de-al doilea tab
            self.gui.get_object('imagemenuitem1').set_label(_('Add a Radio channel'))
        if page == 2: #la selectarea celui de-al treilea tab
            self.gui.get_object('imagemenuitem1').hide()

    def refreshList(self, obj, event=None):
        self.clearChannelCache()
        self.gui.get_object('channelstore').clear()
        self.gui.get_object('radiostore').clear()
        threading.Thread(target=self.getChannels, args=(self.populateList,)).start()

    def loadVideoEQ(self):
        # setup b, c, s sliders
        if hasattr(self, 'currentChannel') \
        and self.currentChannel \
        and self.settingsManager.getVideoEQ_channel(self.currentChannel.id):
            values = self.settingsManager.getVideoEQ_channel(self.currentChannel.id)
        else:
            values = self.settingsManager.getVideoEQ_global()
        self.gui.get_object('brightness_scale').set_value(values['b'])
        self.gui.get_object('contrast_scale').set_value(values['c'])
        self.gui.get_object('saturation_scale').set_value(values['s'])

        # setup aspect ratio combo
        if hasattr(self, 'currentChannel') \
        and self.currentChannel \
        and self.settingsManager.getAspect_channel(self.currentChannel.id):
            aspect = self.settingsManager.getAspect_channel(self.currentChannel.id)
        else:
            aspect = self.settingsManager.getAspect_channel(self.settingsManager.aspectratio)
        iter = self.gui.get_object('aspect_ratios').get_iter_root()
        while iter:
            if self.gui.get_object('aspect_ratios').get_value(iter, 0) == aspect:
                break
            iter = self.gui.get_object('aspect_ratios').iter_next(iter)
        if iter == None:
            iter = self.gui.get_object('aspect_ratios').get_iter_root()
        self.gui.get_object('aspect_ratio_combo').set_active_iter(iter)

    def showVideoEQ(self, obj, event=None):
        self.loadVideoEQ()
        self.gui.get_object('window8').show()
        self.gui.get_object('window8').present()

    def videoEQreset(self, obj, event=None):
        self.loadVideoEQ()
        self.hideVideoEQ(None)

    def hideVideoEQ(self, obj, event=None):
        self.gui.get_object('window8').hide()
        return True

    def saveVideoEQ_channel(self, obj, event=None):
        b = self.gui.get_object('brightness_scale').get_value()
        c = self.gui.get_object('contrast_scale').get_value()
        s = self.gui.get_object('saturation_scale').get_value()
        self.mediaPlayer.adjustImage(b, c, s)
        if hasattr(self, 'currentChannel') and self.currentChannel:
            self.settingsManager.saveVideoEQ_channel(b, c, s, self.currentChannel.id)
            self.settingsManager.saveAspect_channel(
                self.gui.get_object('aspect_ratio_combo').get_active_text(),
                self.currentChannel.id
            )
        else:
            print 'Error saving video EQ settings'
        self.gui.get_object('window8').hide()

    def saveVideoEQ_global(self, obj, event=None):
        b = self.gui.get_object('brightness_scale').get_value()
        c = self.gui.get_object('contrast_scale').get_value()
        s = self.gui.get_object('saturation_scale').get_value()
        self.mediaPlayer.adjustImage(b, c, s)
        self.settingsManager.saveVideoEQ_global(b, c, s)
        self.settingsManager.saveAspect_global(self.gui.get_object('aspect_ratio_combo').get_active_text())
        self.gui.get_object('window8').hide()

    def applyVideoSettings(self, obj=None, event=None):
        if obj == None:                 # set on startup
            if self.gui.get_object('window8').get_property("visible"):
                return True
            self.loadVideoEQ()

        # set video eq
        b = self.gui.get_object('brightness_scale').get_value()
        c = self.gui.get_object('contrast_scale').get_value()
        s = self.gui.get_object('saturation_scale').get_value()

        # set aspect ratio
        active = self.gui.get_object('aspect_ratio_combo').get_active()

        if active == 0:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, float(gtk.gdk.screen_width()) / float(gtk.gdk.screen_height()), False)
        elif active == 1:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1, False)
        elif active == 2:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.5, False)
        elif active == 3:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.33, False)
        elif active == 4:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.25, False)
        elif active == 5:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.55, False)
        elif active == 6:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.4, False)
        elif active == 7:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.77, False)
        elif active == 8:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 1.6, False)
        elif active == 9:
            self.gui.get_object('aspectframe1').set(0.5, 0.5, 2.35, False)
        
        # apply settings to video backend
        self.mediaPlayer.setRatio(active)
        self.mediaPlayer.adjustImage(b, c, s)
        return True

    def showAddStream(self, obj, event=None):
        self.gui.get_object('entry3').set_text('')
        self.gui.get_object('entry4').set_text('')
        self.gui.get_object('entry2').set_text('')
        self.gui.get_object('image23').set_from_file('blank.gif')
        self.gui.get_object('window7').show()

    def hideAddStream(self, obj, event=None):
        self.gui.get_object('window7').hide()
        return True

    def addNewChannel(self, obj, event=None):
        import getpass
        page = self.gui.get_object('notebook2').get_current_page()
        image = self.gui.get_object('image23').get_pixbuf()
        nume = self.gui.get_object('entry3').get_text()
        url = self.gui.get_object('entry4').get_text()
        param = self.gui.get_object('entry2').get_text()
        params = {url : param}
        img = tools.GdkPixbuf_to_Image(image)
        buf = StringIO.StringIO()
        img.save(buf, "PNG")
        imgdata = buf.getvalue()
        conn = sqlite3.connect(os.getenv('HOME') + '/.tvmaxe/userlist.db')
        conn.row_factory = sqlite3.Row
        conn.text_factory = str
        data = conn.cursor()
        data.execute("CREATE TABLE IF NOT EXISTS tv_channels (id, icon, name, streamurls, params, guide, audiochannels)")
        data.execute("CREATE TABLE IF NOT EXISTS radio_channels (id, icon, name, streamurls, params)")
        data.execute("CREATE TABLE IF NOT EXISTS info (name, version, author, url, epgurl)")
        data.execute("INSERT INTO info VALUES (?, ?, ?, ?, ?)", ['Local', '1', getpass.getuser(), '', ''])
        conn.commit()

        if page == 0:
            channelstore = self.gui.get_object('channelstore')
            iter = channelstore.get_iter_root()
            while (iter):
                id = channelstore.get_value(iter, 0)
                if url in self.channels[id].streamurls:
                    dialog = gtk.MessageDialog(parent=self.gui.get_object('window7'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('This channel already exists'));
                    dialog.set_title(_('Error'));
                    resp = dialog.run();
                    dialog.destroy();
                    return
                iter = channelstore.iter_next(iter)
            if nume == '' or url == '':
                dialog = gtk.MessageDialog(parent=self.gui.get_object('window12'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('Name and URL required!'));
                dialog.set_title(_('Error'));
                resp = dialog.run();
                dialog.destroy();
                return
            url = url.translate(string.maketrans("", ""), string.whitespace)
            id = re.sub(r'\W+', '', 'Local::' + nume + str(random.randint(1, 9999)))
            channel = Channel(id = id, icon = image, name = nume, streamurls = [url], params = params, guide = '', audiochannels = '', liststore = channelstore, source = 'Local')
            channel.info['name'] = 'Local'
            iter = self.addChannel(channel, channelstore)
            if iter == None:
                dialog = gtk.MessageDialog(parent=self.gui.get_object('window12'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('Channel cannot be added. Are you sure that the URL is correct?'))
                dialog.set_title(_('Error'))
                resp = dialog.run()
                dialog.destroy()
                return
            data.execute("INSERT INTO tv_channels VALUES (?,?,?,?,?,?,?)", [id, base64.b64encode(imgdata), nume, json.dumps([url]), json.dumps(params), '', json.dumps([])])
            conn.commit()
        if page == 1:
            channelstore = self.gui.get_object('radiostore')
            iter = channelstore.get_iter_root()
            while (iter):
                if url == channelstore.get_value(iter, 2):
                    dialog = gtk.MessageDialog(parent=self.gui.get_object('window7'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('This channel already exists'));
                    dialog.set_title(_('Error'));
                    resp = dialog.run();
                    dialog.destroy();
                    return
                iter = channelstore.iter_next(iter)
            url = url.translate(string.maketrans("", ""), string.whitespace)
            if nume == '' or url == '':
                dialog = gtk.MessageDialog(parent=self.gui.get_object('window12'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('Name and URL required!'));
                dialog.set_title(_('Error'));
                resp = dialog.run();
                dialog.destroy();
                return
            id = re.sub(r'\W+', '', 'Local::' + nume + str(random.randint(1, 9999)))
            channel = Channel(id = id, icon = image, name = nume, streamurls = [url], params = params, guide = '', audiochannels = '', liststore = channelstore, source = 'Local')
            channel.info['name'] = 'Local'
            iter = self.addChannel(channel, channelstore)
            if iter == None:
                dialog = gtk.MessageDialog(parent=self.gui.get_object('window12'), flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=_('Channel cannot be added. Are you sure that the URL is correct?'))
                dialog.set_title(_('Error'))
                resp = dialog.run()
                dialog.destroy()
                return
            data.execute("INSERT INTO radio_channels VALUES (?,?,?,?,?)", [id, base64.b64encode(imgdata), nume, json.dumps([url]), json.dumps(params)])
        self.gui.get_object('entry3').set_text('')
        self.gui.get_object('entry4').set_text('')
        self.gui.get_object('image23').set_from_file('blank.gif')
        self.gui.get_object('window7').hide()

    def deleteChannel(self, obj, event=None):
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
            treeselection = chList.get_selection()
            (model, iter) = self.iterConvert(treeselection.get_selected())
            id = model.get_value(iter, 0)
            model.remove(iter)
        elif page == 1:
            chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            (model, iter) = self.iterConvert(treeselection.get_selected())
            id = model.get_value(iter, 0)
            model.remove(iter)
        else:
            return
        if self.channels[id].info['name'] == 'Local':
            conn = sqlite3.connect(os.getenv('HOME') + '/.tvmaxe/userlist.db')
            data = conn.cursor()
            data.execute("DELETE FROM tv_channels WHERE id=?", (id, ))
            data.execute("DELETE FROM radio_channels WHERE id=?", (id, ))
            conn.commit()
        else:
            self.blacklist.add(self.channels[id])
        blackstore = self.gui.get_object('blackstore')
        blackstore.append([id, self.channels[id].name])
        self.gui.get_object('liststatuslabel').set_text(_("Total: %s channels in %s subscriptions" % (str(self.countChannels()), str(len(self.settingsManager.abonamente)))))

    def iterConvert(self, tup):
        (model, iter) = tup
        iter = model.convert_iter_to_child_iter(iter)
        iter = model.get_model().convert_iter_to_child_iter(None, iter)
        return (model.get_model().get_model(), iter)

    def loginPBX(self, obj, auto = False):
        pbxlogin = self.settingsManager.getPBXuser()
        self.gui.get_object('entry5').set_text(pbxlogin[1])
        self.gui.get_object('entry6').set_text(pbxlogin[2])
        self.gui.get_object('checkbutton3').set_active(pbxlogin[0])
        self.gui.get_object('window9').show()
        if auto:
            self.connectPBX(self.gui.get_object('button32'))
        return False

    def hidePBX(self, obj, event=None):
        if not self.gui.get_object('checkbutton3').get_active():
            self.gui.get_object('entry5').set_text('')
            self.gui.get_object('entry6').set_text('')
            self.settingsManager.savePBX(self.gui.get_object('checkbutton3').get_active(), self.gui.get_object('entry5').get_text(), self.gui.get_object('entry6').get_text())
        else:
            self.settingsManager.savePBX(self.gui.get_object('checkbutton3').get_active(), self.gui.get_object('entry5').get_text(), self.gui.get_object('entry6').get_text())
        self.gui.get_object('window9').hide()
        return True

    def PBXupdateBar(self):
        if self.pbx.nrCanale == 0:
            return True             # reapeleaza functia
        frac = float(self.pbx.nrIncarcate) / float(self.pbx.nrCanale)
        if frac < 1.0:
            self.gui.get_object('progressbar1').set_fraction(frac)
            return True             # reapeleaza functia
        else:
            self.gui.get_object('progressbar1').set_fraction(1.0)
            self.gui.get_object('window9').hide()
            return False            # nu mai reapela

    def connectPBX(self, obj, event=None):
        username = self.gui.get_object('entry5').get_text()
        password = self.gui.get_object('entry6').get_text()
        threading.Thread(target=self.pbx.signIn, args=(username, password, self.getPBX)).start()
        self.gui.get_object('vbox26').set_sensitive(False)
        self.gui.get_object('hbox27').show()
        self.PBXupdateBar_to = gobject.timeout_add(500, self.PBXupdateBar)

    def getPBX(self, chlist):
        if not chlist:
            if hasattr(self, 'PBXupdateBar_to'):
                gobject.source_remove(self.PBXupdateBar_to)
            gobject.idle_add(self.gtkMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, _('Error'), _('Cannot fetch the channel list. Aborting...'))
            gobject.idle_add(self.gui.get_object('vbox26').set_sensitive, True)
            gobject.idle_add(self.gui.get_object('hbox27').hide)
            gobject.idle_add(self.gui.get_object('window9').hide)
            return

        icon = gtk.gdk.pixbuf_new_from_file('PBX.png')
        for x in chlist:
            nume = x[0]
            id = re.sub(r'\W+', '', 'PBX::' + nume)
            url = [x[1]]
            if 'Radio' in nume:
                channelstore = self.gui.get_object('radiostore')
            else:
                channelstore = self.gui.get_object('channelstore')
            channel = Channel(id = id, icon = icon, name = nume, streamurls = url, params = {}, guide = '', audiochannels = [], liststore = channelstore, source = 'PBX TV')
            channel.info = {'name' : 'PBX TV', 'version' : '0.01', 'author' : '', 'url' : 'http://pbxtv.ro/', 'epgurl' : ''}
            self.addChannel(channel, channelstore)

        self.gui.get_object('vbox26').set_sensitive(True)
        self.gui.get_object('hbox27').hide()
        self.gui.get_object('window9').hide()
        if self.gui.get_object('checkbutton3').get_active():
            self.settingsManager.savePBX(self.gui.get_object('checkbutton3').get_active(), self.gui.get_object('entry5').get_text(), self.gui.get_object('entry6').get_text())
        else:
            self.settingsManager.savePBX(self.gui.get_object('checkbutton3').get_active(), '', '')

    def adaugaAbonament(self, obj=None):
        self.gui.get_object('entry8').set_text('')
        self.gui.get_object('window10').show()

    def addSubscription(self, obj):
        url = self.gui.get_object('entry8').get_text()
        self.gui.get_object('liststore1').append([False, url])
        self.settingsManager.abonamente.append([1, url])
        self.gui.get_object('window10').hide()

    def hideAdaugaAbonament(self, obj=None, event=None):
        self.gui.get_object('window10').hide()
        return True

    def editAbonament(self, obj):
        self.gui.get_object('entry10').set_text('')
        lista = self.gui.get_object('treeview4')
        treeselection = lista.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            self.lastSubURLEdit = model.get_value(iter, 1)
            self.gui.get_object('entry10').set_text(self.lastSubURLEdit)
            self.gui.get_object('window11').show()

    def saveEditAbonament(self, obj):
        lista = self.gui.get_object('treeview4')
        treeselection = lista.get_selection()
        (model, iter) = treeselection.get_selected()
        url = self.gui.get_object('entry10').get_text()
        model.set_value(iter, 1, url)
        if url != self.lastSubURLEdit:
            for x in self.settingsManager.abonamente:
                if x[1] == self.lastSubURLEdit:
                    self.settingsManager.abonamente[self.settingsManager.abonamente.index(x)] = [x[0], url]
                    break
            self.lastSubURLEdit = None
            self.settingsManager.updateList = True
        self.gui.get_object('window11').hide()

    def hideEditAbonament(self, obj, event=None):
        self.gui.get_object('entry10').set_text('')
        self.gui.get_object('window11').hide()
        return True

    def stergeAbonament(self, obj):
        lista = self.gui.get_object('treeview4')
        treeselection = lista.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            for x in self.settingsManager.abonamente:
                if x[1] == model.get_value(iter, 1):
                    self.settingsManager.abonamente.pop(self.settingsManager.abonamente.index(x))
                    break
            model.remove(iter)

    def findKey(self, dic, val):
        try:
            return [k for k, v in dic.iteritems() if v == val][0]
        except:
            return None

    def donate(self, obj, event=None):
        webbrowser.open('https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=DZ52GUL3WXQKN&lc=RO&item_name=TV%2dMAXE&no_note=1&no_shipping=1&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted')
        self.donated(None)

    def donated(self, obj, event=None):
        ver = self.settingsManager.saveDonate(version)
        self.gui.get_object('hbox29').hide()

    def showDonate(self):
        v = self.settingsManager.getDonate()
        if float(v) < float(version):
            self.gui.get_object('hbox29').show()

    def hideShowTVMaxe(self, obj, event=None):
        if event.button == 1:
            if self.tvmaxevis:
                if self.radioMode:
                    self.gui.get_object('window13').hide()
                else:
                    self.gui.get_object('window1').hide()
                self.gui.get_object('menuitem29').set_label(_('Show TV-MAXE'))
                self.tvmaxevis = False
            else:
                if self.radioMode:
                    self.gui.get_object('window13').show()
                else:
                    self.gui.get_object('window1').show()
                self.gui.get_object('menuitem29').set_label(_('Hide TV-MAXE'))
                self.tvmaxevis = True
        if event.button == 3:
            if self.mediaPlayer.isPlaying():
                self.gui.get_object('menuitem30').set_sensitive(True)
            else:
                self.gui.get_object('menuitem30').set_sensitive(False)
            self.gui.get_object('menu9').popup(None, None, gtk.status_icon_position_menu, event.button, event.time, self.gui.get_object('statusicon1'))

    def hideShowTVMaxe_Menu(self, obj):
        if self.tvmaxevis:
            if self.radioMode:
                self.gui.get_object('window13').hide()
            else:
                self.gui.get_object('window1').hide()
            self.gui.get_object('menuitem29').set_label(_('Show TV-MAXE'))
            self.tvmaxevis = False
        else:
            if self.radioMode:
                self.gui.get_object('window13').show()
            else:
                self.gui.get_object('window1').show()
            self.gui.get_object('menuitem29').set_label(_('Hide TV-MAXE'))
            self.tvmaxevis = True

    def statusIconVolume(self, obj, event):
        if event.direction.value_name == 'GDK_SCROLL_DOWN':
            gobject.idle_add(self.setVolume, None, None, -0.1)
        elif event.direction.value_name == 'GDK_SCROLL_UP':
            gobject.idle_add(self.setVolume, None, None, 0.1)

    def createTrayMenus(self):
        # parent menus
        tvs = gtk.Menu()
        radios = gtk.Menu()
        parents = {'tv' : {}, 'radio' : {}}
        items = {'tv' : {}, 'radio' : {}}
        model = self.gui.get_object('chlist_combo')
        iter = model.iter_next(model.get_iter_root())   # skip "All" list
        while iter:
            nume = model.get_value(iter, 0)
            item = gtk.MenuItem(nume)
            submenu = gtk.Menu()
            item.set_submenu(submenu)
            tvs.append(item)
            items['tv'][nume] = item
            parents['tv'][nume] = submenu
            item = gtk.MenuItem(nume)
            submenu = gtk.Menu()
            item.set_submenu(submenu)
            radios.append(item)
            items['radio'][nume] = item
            parents['radio'][nume] = submenu
            iter = model.iter_next(iter)
        # radio menus
        model = self.gui.get_object('radiostore')
        iter = model.get_iter_root()
        while iter:
            nume = model.get_value(iter, 2)
            item = gtk.MenuItem(nume)
            channel = self.channels[model.get_value(iter, 0)]
            item.connect("activate", self.trayplay, self.playRadioChannel, channel)
            parents['radio'][channel.source].append(item)
            items['radio'][channel.source].show()
            item.show()
            iter = model.iter_next(iter)
        # tv menus
        model = self.gui.get_object('channelstore')
        menu = gtk.Menu()
        iter = model.get_iter_root()
        while iter:
            nume = model.get_value(iter, 2)
            item = gtk.MenuItem(nume)
            channel = self.channels[model.get_value(iter, 0)]
            item.connect("activate", self.trayplay, self.playRadioChannel, channel)
            parents['tv'][channel.source].append(item)
            items['tv'][channel.source].show()
            item.show()
            iter = model.iter_next(iter)

        self.gui.get_object('menuitem38').remove_submenu()
        self.gui.get_object('menuitem38').set_submenu(radios)
        self.gui.get_object('menuitem41').remove_submenu()
        self.gui.get_object('menuitem41').set_submenu(radios)
        self.gui.get_object('menuitem39').remove_submenu()
        self.gui.get_object('menuitem39').set_submenu(tvs)
        return False

    def trayplay(self, obj, func, t):
        if self.getTime_to:
            gobject.source_remove(self.getTime_to)
        iter = t.get_iter()
        if func == self.playChannel:
            model = self.gui.get_object('channelstore')
            path = model.get_path(iter)
            treeselection = self.gui.get_object('treeview1').get_selection()
            treeselection.select_path(path)
        if func == self.playRadioChannel:
            model = self.gui.get_object('radiostore')
            path = model.get_path(iter)
            treeselection = self.gui.get_object('treeview3').get_selection()
            treeselection.select_path(path)
        threading.Thread(target=func, args=(t, )).start()

    def channelInfo(self, obj):
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            chList = self.gui.get_object('treeview1')
            treeselection = chList.get_selection()
            selected = treeselection.get_selected()
            (model, iter) = treeselection.get_selected()
            id = model.get_value(iter, 0)
            nume = self.channels[id].name
            abonament = self.channels[id].info['name']
            adresa = '\n'.join(self.channels[id].streamurls)
            icon = self.channels[id].icon
            if adresa.startswith('sop:'):
                protocol = 'SopCast'
            else:
                gp = adresa.split('://')
                protocol = gp[0].upper()
            valabilitate = ''
            chid = self.channels[id].guide
        elif page == 1:
            chList = self.gui.get_object('treeview3')
            treeselection = chList.get_selection()
            selected = treeselection.get_selected()
            (model, iter) = treeselection.get_selected()
            id = model.get_value(iter, 0)
            nume = self.channels[id].name
            abonament = self.channels[id].info['name']
            adresa = '\n'.join(self.channels[id].streamurls)
            icon = self.channels[id].icon
            if adresa.startswith('sop:'):
                protocol = 'SopCast'
            else:
                gp = adresa.split('://')
                protocol = gp[0].upper()
            valabilitate = ''
            chid = ''
        if chid != '':
            self.gui.get_object('button43').set_sensitive(True)
        else:
            self.gui.get_object('button43').set_sensitive(False)
        self.gui.get_object('button42').set_sensitive(True)
        self.gui.get_object('button42').set_label(_('Report as broken'))
        self.gui.get_object('image22').set_from_pixbuf(icon)
        self.gui.get_object('label59').set_label(nume)
        self.gui.get_object('label72').set_label(abonament)
        self.gui.get_object('label74').set_label(protocol)
        self.gui.get_object('label76').set_label(adresa)
        self.gui.get_object('label78').set_label('')
        self.gui.get_object('window12').show()
        if hasattr(self, 'channelInfo_showGhidTV_handler'):
            self.gui.get_object('button43').disconnect(self.channelInfo_showGhidTV_handler)
        self.channelInfo_showGhidTV_handler = self.gui.get_object('button43').connect('clicked', self.channelInfo_showGhidTV, self.channels[id])
        threading.Thread(target=self.valabilitate, args=(adresa, self.channelInfo_status)).start()

    def changeAudioTrack(self, obj, trackid):
        self.mediaPlayer.changeAudio(trackid)

    def blmanager(self, obj):
        self.blacklist.showGUI(self.gui)

    def hideblmanager(self, obj, event = None):
        self.blacklist.hideGUI()
        return True

    def removeBlacklisted(self, obj, event = None):
        id = self.blacklist.remove()
        channelstore = self.gui.get_object('channelstore')
        radiostore = self.gui.get_object('radiostore')
        if not id:
            return
        if not self.channels.has_key(id):
            return
        if self.channels[id].liststore == channelstore:
            self.addChannel(self.channels[id], channelstore)
        elif self.channels[id].liststore == radiostore:
            self.addChannel(self.channels[id], radiostore)

    def blclear(self, obj, event = None):
        channelstore = self.gui.get_object('channelstore')
        radiostore = self.gui.get_object('radiostore')
        ids = self.blacklist.clear()
        for id in ids:
            if self.channels[id].liststore == channelstore:
                self.addChannel(self.channels[id], channelstore)
            elif self.channels[id].liststore == radiostore:
                self.addChannel(self.channels[id], radiostore)

    def channelInfo_status(self, status):
        self.gui.get_object('label78').set_label(status)
        return False

    def hideChannelInfo(self, obj, event=None):
        self.gui.get_object('window12').hide()
        return True

    def channelInfo_showGhidTV(self, obj, channel):
        self.showGhidTV(None, channel)
        self.updateEPG(None)

    def valabilitate(self, url, callback):
        try:
            req = urllib2.Request(basehost + '/report.php?get=' + url)
            response = urllib2.urlopen(req)
            data = int(response.read())
            if data > 5:
                idle = gobject.idle_add(callback, '<span foreground="#FF0000">' + _('appears to be broken') + '</span>')
            else:
                idle = gobject.idle_add(callback, 'OK')
        except:
            idle = gobject.idle_add(callback, 'OK')

    def channelInfo_raporteaza(self, obj):
        obj.set_label(_('Reported'))
        obj.set_sensitive(False)
        threading.Thread(target=self.reportChannel, args=(self.gui.get_object('label76').get_label(),)).start()

    def reportChannel(self, url):
        try:
            req = urllib2.Request(basehost + '/report.php?set=' + url)
            response = urllib2.urlopen(req)
            print response.read()
        except:
            pass

    def addChanel_selectIcon(self, obj):
        chooser = gtk.FileChooserDialog(title=_('Select image file...'),action=gtk.FILE_CHOOSER_ACTION_OPEN,
                          buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name(_("Images"))
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.gif")
        chooser.add_filter(filter)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        else:
            chooser.destroy()
            return
        chooser.destroy()
        im = Image.open(filename)
        im.thumbnail((24, 24), Image.ANTIALIAS)
        pixbuf = tools.Image_to_GdkPixbuf(im)
        self.gui.get_object('image23').set_from_pixbuf(pixbuf)

    def getCurrentChannelInfo(self):
        if not self.currentChannel:
            return None
        info = {'name' : self.currentChannel.name,
                'status' : self.gui.get_object('label65').get_text(),
                'chid' : self.currentChannel.guide,
                'tvguide' :  self.tvguide.getCurrent}
        return info

    def getChannelList(self, t):
        l = {}
        if t == 'tv':
            model = self.gui.get_object('channelstore')
        elif t == 'radio':
            model = self.gui.get_object('radiostore')
        iter = model.get_iter_root()
        while iter:
            id = model.get_value(iter, 0)
            nume = self.channels[id].name
            url = self.channels[id].streamurls[0]
            l[url] = nume
            iter = model.iter_next(iter)
        return l

    def addabo(self, abo):
        model = self.gui.get_object('chlist_combo')
        iter = model.get_iter_root()
        while iter:
            if model.get_value(iter, 0) == abo:
                return
            iter = model.iter_next(iter)
        model.append([abo])
        return False

    def refilter(self, obj):
        i = obj.get_active()
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            self.gui.get_object('combobox5').set_active(i)
        if page == 1:
            self.gui.get_object('combobox4').set_active(i)
        self.channelfilter.refilter()
        self.radiofilter.refilter()

    def sortme(self, model, iter, data=None):
        id = model.get_value(iter, 0)
        if not id:
            return
        abo = self.channels[id].source
        page = self.gui.get_object('notebook2').get_current_page()
        if page == 0:
            f = self.gui.get_object('combobox4').get_active_text()
        if page == 1:
            f = self.gui.get_object('combobox5').get_active_text()
        if f == _('All'):
            return True
        if f == abo:
            return True
        else:
            return False
        return True

    def listError(self):
        return
        #self.gtkMessage(gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, _('Error'), _('Cannot fetch the channel list. Aborting...'))

    def countChannels(self, liststore = None):
        count = 0
        if liststore:
            iter = liststore.get_iter_root()
            while iter:
                count += 1
                iter = liststore.iter_next(iter)
            return count
        else:
            liststores = [self.gui.get_object('channelstore'), self.gui.get_object('radiostore')]
            count = 0
            for liststore in liststores:
                iter = liststore.get_iter_root()
                while iter:
                    count += 1
                    iter = liststore.iter_next(iter)
            return count

    def browseSubscription(self, obj):
        chooser = gtk.FileChooserDialog(title=_('Select subscription file...'),action=gtk.FILE_CHOOSER_ACTION_OPEN,
                          buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        else:
            chooser.destroy()
            return
        chooser.destroy()
        self.gui.get_object('entry8').set_text('file://' + filename)

    def saveChannellist(self, obj):
        chooser = gtk.FileChooserDialog(title=_('Save current channellist...'),action=gtk.FILE_CHOOSER_ACTION_SAVE,
                          buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_do_overwrite_confirmation(True)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        else:
            chooser.destroy()
            return
        chooser.destroy()
        if os.path.exists(filename):
            os.remove(filename)
        conn = sqlite3.connect(filename)
        conn.row_factory = sqlite3.Row
        conn.text_factory = str
        data = conn.cursor()
        data.execute("CREATE TABLE IF NOT EXISTS tv_channels (id, icon, name, streamurls, params, guide, audiochannels)")
        data.execute("CREATE TABLE IF NOT EXISTS info (name, version, author, url, epgurl)")
        data.execute("CREATE TABLE IF NOT EXISTS radio_channels (id, icon, name, streamurls, params)")
        conn.commit()

        model = self.gui.get_object('treeview1').get_model()
        iter = model.get_iter_root()
        while iter:
            id = model[iter][0]
            channel = self.channels[id]
            icon = tools.GdkPixbuf_to_Image(channel.icon)
            buf = StringIO.StringIO()
            icon.save(buf, "PNG")
            imgdata = buf.getvalue()
            data.execute("INSERT INTO tv_channels VALUES (?,?,?,?,?,?,?)", [id, base64.b64encode(imgdata), channel.name, json.dumps(channel.streamurls), json.dumps(channel.params), channel.guide, json.dumps(channel.audiochannels)])
            iter = model.iter_next(iter)
        conn.commit()

        model = self.gui.get_object('treeview3').get_model()
        iter = model.get_iter_root()
        while iter:
            id = model[iter][0]
            channel = self.channels[id]
            icon = tools.GdkPixbuf_to_Image(channel.icon)
            buf = StringIO.StringIO()
            icon.save(buf, "PNG")
            imgdata = buf.getvalue()
            data.execute("INSERT INTO radio_channels VALUES (?,?,?,?,?)", [id, base64.b64encode(imgdata), channel.name, json.dumps(channel.streamurls), json.dumps(channel.params)])
            iter = model.iter_next(iter)
        conn.commit()
        self.statusbar(_('Channellist was successfully saved.'))

    def clearChannelCache(self):
        files = os.listdir(tvmaxedir + 'cache/')
        for file in files:
            os.remove(tvmaxedir + 'cache/' + file)

    def buildComboDays(self):
        romana =[_('Sunday'), _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday')]
        today = datetime.date.today()
        self.gui.get_object('liststore3').clear()
        for x in range(0, 7):
            zile = datetime.timedelta(days=x)
            zinoua = today + zile
            nrzi = int(zinoua.strftime("%w"))
            zinouaday = str(zinoua.day)
            lunanoua = str(zinoua.month)
            if len(zinouaday) == 1:
                zinouaday = '0' + zinouaday
            if len(lunanoua) == 1:
                lunanoua = '0' + lunanoua
            datanoua = zinouaday + '.' + lunanoua + '.' +  str(zinoua.year)
            iter = self.gui.get_object('liststore3').append([romana[nrzi] + ', ' + datanoua, datanoua.replace('.', '-')])
            if x == 0:
                self.gui.get_object('combobox3').set_active_iter(iter)

    def protocolPorts(self):
        if hasattr(self, 'settingsManager'):
            if self.settingsManager.staticports:
                inport, outport = (self.settingsManager.inport, self.settingsManager.outport)
            else:
                inport, outport = (random.randint(10025, 65535), random.randint(10025, 65535))
        else:
            inport, outport = (random.randint(10025, 65535), random.randint(10025, 65535))
        return (inport, outport)

    def readTheme(self, obj=None, event=None):
        themedir = self.settingsManager.getTheme()
        themefile = themedir + '/theme'
        default = os.path.dirname(os.path.realpath(__file__)) + '/themes/default'
        themedata = self.StatusImage.themedata
        if os.path.exists(themefile):
            fh = open(themefile)
            for line in fh.readlines():
                line = line.rstrip()
                if line.startswith('loading'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['loading'] = themedir + '/' + param
                if line.startswith('error'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['error'] = themedir + '/' + param
                if line.startswith('logo'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['logo'] = themedir + '/' + param
                if line.startswith('showtext'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['showtext'] = param
                if line.startswith('color'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['color'] = param
                if line.startswith('font'):
                    param = line.split('=', 1)[1].lstrip()
                    themedata['font'] = themedir + '/' + param
        self.StatusImage.updateTheme(themedata)

    def tvguide_popmenu(self, obj, event=None):
        if event and event.button == 3:
            treeview = self.gui.get_object('treeview2')
            path = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path:
                self.gui.get_object('guideMenu').popup(None, None, None, event.button, event.time)

    def showScheduler(self, obj, event=None):
        treeview = self.gui.get_object('treeview2')
        treeselection = treeview.get_selection()
        model_iter = treeselection.get_selected()
        if obj == self.gui.get_object('button58'):
            self.Scheduler.show((None, None))
        else:
            self.Scheduler.show(model_iter)

    def hideScheduler(self, obj, event=None):
        return self.Scheduler.hide()

    def addScheduler(self, obj, event=None):
        self.Scheduler.add()

    def editSchedule(self, obj, event=None):
        treeview = self.gui.get_object('treeview7')
        treeselection = treeview.get_selection()
        model_iter = treeselection.get_selected()
        self.Scheduler.show(model_iter)

    def removeSchedule(self, obj, event=None):
        treeview = self.gui.get_object('treeview7')
        treeselection = treeview.get_selection()
        model_iter = treeselection.get_selected()
        if iter:
            self.Scheduler.remove(model_iter)

    def showSchedMan(self, obj, event=None):
        self.Scheduler.showManager()

    def hideSchedMan(self, obj, event=None):
        return self.Scheduler.hideManager()

    def autoplay(self):
        if self.autostart:
            if self.autostart in self.channels:
                self.playChannel(self.channels[self.autostart])
            else:
                tools.msg_error("Sorry, but this channel does not exists.")
                self.stop()
        return False

    def saveRecord(self, tip):
        dialog = gtk.FileChooserDialog("Save recording...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        predefname = str(datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))
        if tip == 'audio':
            dialog.set_current_name(predefname + '.mp3')
        elif tip == 'video':
            format = self.settingsManager.getFormat()
            if len(format) == 3:
                ext = format.lower()
            elif format == 'matroska':
                ext = 'mkv'
            else:
                ext = 'avi'
            dialog.set_current_name(predefname + '.' + ext)
        dialog.set_local_only = True
        if self.Recorder.saveAs:
            dialog.set_current_folder(os.path.split(self.Recorder.saveAs)[0])
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.lastSavedRecording = dialog.get_uri()
            dialog.destroy()
            return self.lastSavedRecording
        dialog.destroy()
        return None

    def blinkRecord(self):
        if self.gui.get_object('recordbox').props.visible == True:
            self.gui.get_object('recordbox').hide()
        else:
            self.gui.get_object('recordbox').show()
        if not self.recordingMode:
            self.gui.get_object('recordbox').hide()
        return self.recordingMode

    def showDiagnostics(self, obj):
        self.diags = Diagnostics(self.gui)
        self.diags.settingsManager = self.settingsManager
        self.diags.show()

    def closeDiagnostics(self, obj, event=None):
        if hasattr(self, 'diags'):
            self.diags.close()
        return True

    def runDiagnostics(self, obj):
        if hasattr(self, 'diags'):
            self.diags.run()

    def diagnosticSelect(self, obj):
        if hasattr(self, 'diags'):
            treeselection = obj.get_selection()
            model_iter = treeselection.get_selected()
            self.diags.show_details(model_iter[1])

    def quit(self, obj=None, event=None):
        self.mediaPlayer.quit()
        if hasattr(self, 'infrared'):
            self.infrared.quit()
        for x in self.protocols:
            self.protocols[x].stop()
            self.protocols[x].quit()
        if os.path.exists('/tmp/tvmx_tmp_db'):
            os.remove('/tmp/tvmx_tmp_db')
        sizes = self.gui.get_object('window1').get_size()
        self.settingsManager.saveWindowSize(sizes[0], sizes[1])
        hpaned = self.gui.get_object('hpaned1').get_position()
        self.settingsManager.saveHPanedPosition(hpaned)
        self.settingsManager.saveVolume()
        self.SocketServer.close()
        self.StatusImage.clean()
        self.Recorder.quit()
        os._exit(0)

    def initHTTPRemote(self):
        return remoteC.HTTPRemoteControl(self,
                chchannel = self.playURL,
                volume = self.setVolume,
                mute = self.mute,
                stop = self.stop,
                channelinfo = self.getCurrentChannelInfo)

    def getVersion(self):
        return version

    def main(self):
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()

if __name__ == "__main__":
    channelID = None
    if '--start-channel' in sys.argv:
        channelID = sys.argv[sys.argv.index('--start-channel') + 1]
        print 'Starting TV-Maxe with ' + channelID
    main = TVMaxe(channelID)
    main.main()
