import sys, os, subprocess, gobject, gtk, tools, pickle, random, copy
from daemon import TDaemon
from channel import Channel
from dateutil import parser

orar_file = os.getenv("HOME") + '/.tvmaxe/schedule'

class Scheduler:
    def __init__(self, tvmaxepy, tvmaxe):
        self.daemon = TDaemon(tvmaxepy)
        self.gui = tvmaxe.gui
        self.channels = tvmaxe.channels
        self.orar = {}
        if os.path.exists(orar_file):
            print 'Loading schedules file...'
            try:
                fh = open(orar_file, 'rb')
                self.orar = pickle.load(fh)
            except TypeError:
                # we had a bug here with incorrectly saved schedule pickle, so
                # this exceptions probably means that we're using the wrong file
                os.remove(orar_file)
            finally:
                fh.close()

    def show(self, model_iter):
        model, iter = model_iter
        channel = None
        self.id = None
        if iter:
            if model == self.gui.get_object('scheduleStore'):
                self.id = model[iter][0]
                if self.channels.has_key(model[iter][5]):
                    channel = self.channels[model[iter][5]]
                ceas = model[iter][1]
                ora = int(ceas.split(':')[0])
                minut = int(ceas.split(':')[1])
                nume = model[iter][2]
            else:
                ceas = model[iter][0]
                ora = int(ceas.split(':')[0])
                minut = int(ceas.split(':')[1])
                nume = model[iter][1]
            self.gui.get_object('scheduler_name').set_text(nume)
            self.gui.get_object('schedule_HH').set_value(ora)
            self.gui.get_object('schedule_MM').set_value(minut)
            if not channel:
                self.gui.get_object('scheduler_cbChannels').set_active_iter(tools.search_iter(self.gui.get_object('scheduler_cbChannels').get_model(), 0,
                    self.gui.get_object('combobox2').get_active_text()))
            else:
                self.gui.get_object('scheduler_cbChannels').set_active_iter(tools.search_iter(self.gui.get_object('scheduler_cbChannels').get_model(), 0,
                    channel.id))
            self.gui.get_object('schedule_cbDay').set_active(self.gui.get_object('combobox3').get_active())
        else:
            self.gui.get_object('scheduler_name').set_text('')
            self.gui.get_object('schedule_HH').set_value(7)
            self.gui.get_object('schedule_MM').set_value(0)
            self.gui.get_object('scheduler_cbChannels').set_active(1)
            self.gui.get_object('schedule_cbDay').set_active(0)
        self.gui.get_object('scheduler_w').show()

    def hide(self):
        self.gui.get_object('scheduler_w').hide()
        return True
        
    def showManager(self, reallyShow=True):
        store = self.gui.get_object('scheduleStore')
        store.clear()
        for s in self.orar:
            item = self.orar[s]
            if self.channels.has_key(item['channel'].id):
                store.append([s, item['time'].strftime("%H:%M"), item['name'], item['channel'].name, self.channels[item['channel'].id].icon, item['channel'].id])
        if reallyShow:
            self.gui.get_object('scheduleMan_w').show()
        
    def hideManager(self):
        self.gui.get_object('scheduleMan_w').hide()
        return True
    
    def add(self):
        name = self.gui.get_object('scheduler_name').get_text()
        hh = self.gui.get_object('schedule_HH').get_value()
        mm = self.gui.get_object('schedule_MM').get_value()
        day = self.gui.get_object('schedule_cbDay').get_active_text()
        date = parser.parse(day + ' ' + str(hh) + ':' + str(mm))
        if self.id:
            id = self.id
        else:
            id = name + str(random.random())
        channel = copy.copy(self.channels[self.gui.get_object('scheduler_cbChannels').get_active_text()])
        channel.icon = None # save some RAM by avoiding importing gtk when deserialize with pickle
        channel.liststore = None # save some RAM by avoiding importing gtk when deserialize with pickle
        item = {'name' : name,
            'time' : date,
            'channel' : channel}
        self.orar[id] = item
        self.saveOrar()
        self.hide()
        self.showManager(False)
        del channel
        
    def remove(self, model_iter):
        (model, iter) = model_iter
        del(self.orar[model[iter][0]])
        model.remove(iter)
        self.saveOrar()
        
    def saveOrar(self):
        fh = open(orar_file, 'wb')
        pickle.dump(self.orar, fh, -1)
        fh.close()
        self.startStopDaemon()

    def startStopDaemon(self):
        tvmaxedir = os.getcwd()
        os.chdir('daemon')
        action = None
        if len(self.orar) > 0:
            if os.path.exists('/tmp/tvmaxed.pid'):
                action = None
            else:
                print 'Starting TV-Maxe daemon...'
                action = 'start'
        else:
            print 'Stopping TV-Maxe daemon...'
            action = 'stop'
        if action:
            subprocess.Popen([sys.executable, 'tvmaxed.py', tvmaxedir + '/tvmaxe.py', action])
        os.chdir('..')
