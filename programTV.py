import threading, urllib2, time, datetime, re, itertools, gobject, json

class ProgramTV:
    def __init__(self):
        self.ghidTV = None
        self.guides = {}
        
    def getCurrent(self, channel, callback):
        self.displayEPG = callback
        channelName = channel.name
        today = datetime.date.today()
        zi = str(today.day)
        if len(zi) == 1:
            zi = '0' + zi
        luna = str(today.month)
        if len(luna) == 1:
            luna = '0' + luna
        an = str(today.year)
        datanoua = zi + '-' + luna + '-' + an
        if self.guides.has_key(channelName + '::' + datanoua):
            self.parseCurrent(self.guides[channelName + '::' + datanoua], channelName)
        else:
            threading.Thread(target=self.getGuideData, args=(datanoua, channel, self.parseCurrent)).start()
        
    def parseCurrent(self, data, channelName, callback = None):
        if not callback:
            callback = self.displayEPG
        if type(callback) == str:
            callback = self.displayEPG
        if not data:
            gobject.idle_add(callback, None, channelName)
            return
        ore = []
        for x in data:
            ore.append(x[0])
        ore.sort()
        mimin = datetime.timedelta(seconds=-1)
        H = str(time.strftime("%H", time.localtime()))
        M = int(time.strftime("%M", time.localtime()))
        if M != 59:
            M = str(M+1)
        else:
            M = str(M)
        if len(M) == 1:
            M = '0' + M
        acum = datetime.datetime.strptime(H+':'+M , "%H:%M")
        try:
            apro = [x for x in itertools.takewhile( lambda t: acum > datetime.datetime.strptime(t, "%H:%M"), ore )][-1]
        except IndexError:
            gobject.idle_add(callback, None, channelName)
            return
        for x in data:
            if x[0] == apro:
                gobject.idle_add(callback, x[1], channelName)
                return
           
    def getGuideData(self, day, channel, callback):
        chname = channel.name
        epgurl = channel.info['epgurl']
        codename = channel.guide
        if self.guides.has_key(chname + '::' + day):
            gobject.idle_add(callback, self.guides[chname + '::' + day], chname, day)
            return
        try:
            req = urllib2.Request(epgurl + '?action=getGuide&channel=' + codename + '&date=' + day)
            print epgurl + '?action=getGuide&channel=' + codename + '&date=' + day
            response = urllib2.urlopen(req)
            data = response.read()
            array = json.loads(data)
            for row in array:
                row[0] = self.toLocalTime(row[0])
                self.guides[chname + '::' + day] = array
            gobject.idle_add(callback, array, chname, day)
        except Exception, e:
            gobject.idle_add(callback, None, None, None)
                
    def getPgDetails(self, identificator, callback):
        try:
            req = urllib2.Request('http://tv-maxe.org/services/epg.php?action=getDetails&identificator=' + identificator)
            res = urllib2.urlopen(req)
            data = json.loads(res.read())
            title = data[0]
            detalii = data[2]
            if data[1] != '':
                req = urllib2.urlopen(data[1])
                image = req.read()
            else:
                image = None
            gobject.idle_add(callback, [image, title, detalii], identificator)
        except Exception, e:
            gobject.idle_add(callback, None, identificator)
            
    def minutesLeft(self, channel):
        today = datetime.date.today()
        zi = str(today.day)
        if len(zi) == 1:
            zi = '0' + zi
        luna = str(today.month)
        if len(luna) == 1:
            luna = '0' + luna
        an = str(today.year)
        datanoua = zi + '-' + luna + '-' + an
        channelName = channel.name
        if self.guides.has_key(channelName + '::' + datanoua):
            data = self.guides[channelName + '::' + datanoua]
            ore = []
            for x in data:
                ore.append(x[0])
            ore.sort()
            mimin = datetime.timedelta(seconds=-1)
            H = str(time.strftime("%H", time.localtime()))
            M = int(time.strftime("%M", time.localtime()))
            if M != 59:
                M = str(M+1)
            else:
                M = str(M)
            if len(M) == 1:
                M = '0' + M
            acum = datetime.datetime.strptime(H+':'+M , "%H:%M")
            try:
                apro = [x for x in itertools.takewhile( lambda t: acum > datetime.datetime.strptime(t, "%H:%M"), ore )][-1]
            except IndexError:
                return
            iteration = 0
            for x in data:
                if x[0] == apro:
                    curent = x[0]
                    now = datetime.datetime.time(datetime.datetime.now())
                    acum = str(now.hour) + ':' + str(now.minute)
                    urmeaza = data[iteration+1][0]
                    diff = datetime.datetime.strptime(urmeaza, '%H:%M') - datetime.datetime.strptime(acum, '%H:%M')
                    diff2 = datetime.datetime.strptime(urmeaza, '%H:%M') - datetime.datetime.strptime(curent, '%H:%M')
                    percent = float(diff.seconds) / float(diff2.seconds)
                    percent = 1 - percent
                    return [time.strftime('%H:%M', time.gmtime(diff.seconds)), percent]
                iteration += 1
            return -1
        else:
            return -1
        
    def remove_html_tags(self, data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)
        
    def remove_extra_spaces(self, data):
        p = re.compile(r'\s+')
        return p.sub(' ', data)
        
    def toLocalTime(self, hour):
        diff = time.timezone
        diff = -diff
        now = datetime.datetime.strptime(hour, "%H:%M")
        delta = datetime.timedelta(seconds=diff)
        newtime = now + delta
        h = str(newtime.hour)
        m = str(newtime.minute)
        if len(h) == 1:
            h = '0' + h
        if len(m) == 1:
            m = '0' + m
        return h + ':' + m
