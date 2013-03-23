import workerpool, urllib2, gobject, os

class IconDownloader(workerpool.Job):
	def __init__(self, basehost, channel, imageurl, callback):
		self.basehost = basehost
		self.channel = channel
		self.imageurl = imageurl
		self.callback = callback
		
		if not os.path.exists(os.environ['HOME'] + '/.tvmaxe'):
			os.mkdir(os.environ['HOME'] + '/.tvmaxe')
		if not os.path.exists(os.environ['HOME'] + '/.tvmaxe/cache'):
			os.mkdir(os.environ['HOME'] + '/.tvmaxe/cache')
	
	def run(self):
		imageurl = self.imageurl
		if imageurl == '':
			return
		basehost = self.basehost
		if not os.path.exists(os.environ['HOME'] + '/.tvmaxe/cache/' + os.path.basename(imageurl)):
			if imageurl.startswith('http://'):
			  	req = urllib2.Request(imageurl)
				response = urllib2.urlopen(req)
			else:
				req = urllib2.Request(basehost + imageurl)	# deprecated...
				response = urllib2.urlopen(req)
			imgdata = response.read()
			fh = open(os.environ['HOME'] + '/.tvmaxe/cache/' + os.path.basename(imageurl), 'wb')
			fh.write(imgdata)
			fh.close()
		else:
			fh = open(os.environ['HOME'] + '/.tvmaxe/cache/' + os.path.basename(imageurl), 'rb')
			imgdata = fh.read()
			fh.close()
		gobject.idle_add(self.callback, self.channel, imgdata)
