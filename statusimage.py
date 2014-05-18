import gtk, gobject, StringIO, os, tempfile
from PIL import Image, ImageDraw, ImageFont

class StatusImage:
	def __init__(self):
		default = os.path.dirname(os.path.realpath(__file__)) + '/themes/default'
		self.themedata = {'loading' : default + '/incarca.jpg',
				  'error' : default + '/error.jpg',
				  'logo' : default + '/logo.jpg',
				  'showtext' : 'true',
				  'color' : '#FFFFFF',
				  'font': default + '/DejaVuLGCSans-Bold.ttf'}
		self.width = 0
		self.height = 0
		self.text = ''
		self.logo = ''

	def updateTheme(self, data):
		default = os.path.dirname(os.path.realpath(__file__)) + '/themes/default'
		self.themedata = data
		if not os.path.exists(self.themedata['loading']):
			self.themedata['loading'] = default + '/incarca.jpg'

		if not os.path.exists(self.themedata['error']):
			self.themedata['error'] = default + '/error.jpg'

		if not os.path.exists(self.themedata['logo']):
			self.themedata['logo'] = default + '/logo.jpg'

		if os.path.exists(self.themedata['font']):
			self.font = ImageFont.truetype(self.themedata['font'], 24)
		else:
			self.font = ImageFont.truetype(default + '/DejaVuLGCSans-Bold.ttf', 24)

		self.color = self.themedata['color']
		self.showtext = True
		if self.themedata['showtext'] == 'false':
			self.showtext = False
		if hasattr(self, 'temp'):
			os.unlink(self.temp)
			del self.temp

	def draw(self, drawingarea, text = '', logo = 'logo'):
		logo = self.themedata[logo]
		x, y, width, height = drawingarea.get_allocation()
		if hasattr(self, 'temp') and text == self.text and hasattr(self, 'pixbuf'):
			pixbuf = self.pixbuf.scale_simple(width,height,gtk.gdk.INTERP_BILINEAR)
			gobject.idle_add(self.showimg, drawingarea, pixbuf)
			return
		handle, self.temp = tempfile.mkstemp('.png')
		self.width = width
		self.height = height
		self.logo = logo
		self.text = text
		im = Image.open(logo)
		draw = ImageDraw.Draw(im)
		if self.showtext:
			if type(text) == str or type(text) == unicode:
				tw, th = draw.textsize(text, font=self.font)
				draw.text(((im.size[0]-tw)/2, im.size[1]-50), text, self.color, font=self.font)
			elif type(text) == list:
				row = 0
				for x in text:
					tw, th = draw.textsize(x, font=self.font)
					draw.text(((im.size[0]-tw)/2, row*th+50), x, self.color, font=self.font)
					row += 1
		im.save(self.temp)
		self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.temp)
		pixbuf = self.pixbuf.scale_simple(width,height,gtk.gdk.INTERP_TILES)
		gobject.idle_add(self.showimg, drawingarea, pixbuf)

	def showimg(self, drawingarea, pixbuf):
		gc = drawingarea.window.new_gc()
		drawingarea.window.draw_pixbuf(gc, pixbuf, 0, 0, 0, 0, -1, -1, gtk.gdk.RGB_DITHER_NONE, 0, 0)
		return False

	def clean(self):
		os.unlink(self.temp)
