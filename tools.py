# -*- coding: utf-8 -*-
# Copyright © 2004, 2007 Red Hat, Inc.
# Contribuitors:
# Thomas Woerner <twoerner@redhat.com>
# Florian Festi <ffesti@redhat.com>

import dateutil

__all__ = ["label_set_autowrap"]


def label_set_autowrap(widget):
    """Make labels automatically re-wrap if their containers are resized.
    Accepts label or container widgets."""
    import gtk

    if isinstance(widget, gtk.Container):
        children = widget.get_children()
        for i in xrange(len(children)):
            label_set_autowrap(children[i])
    elif isinstance(widget, gtk.Label) and widget.get_line_wrap():
        widget.connect_after("size-allocate", __label_size_allocate)


def __label_size_allocate(widget, allocation):
    """Callback which re-allocates the size of a label."""
    import pango
    layout = widget.get_layout()

    (lw_old, lh_old) = layout.get_size()

    # fixed width labels

    if lw_old / pango.SCALE == allocation.width:
        return

    # set wrap width to the pango.Layout of the labels ###

    layout.set_width(allocation.width * pango.SCALE)
    (lw, lh) = layout.get_size()

    if lh_old != lh:
        widget.set_size_request(-1, lh / pango.SCALE)

def Image_to_GdkPixbuf(image):
	import gtk, cStringIO
	file = cStringIO.StringIO()
	image.save(file, 'png')
	contents = file.getvalue()
	file.close()
	loader = gtk.gdk.PixbufLoader ('png')
	loader.write (contents, len (contents))
	pixbuf = loader.get_pixbuf ()
	loader.close()
	return pixbuf
	
def GdkPixbuf_to_Image(pb):
        from PIL import Image
	import gtk
	assert(pb.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
	dimensions = pb.get_width(), pb.get_height()
	stride = pb.get_rowstride()
	pixels = pb.get_pixels()
	mode = pb.get_has_alpha() and "RGBA" or "RGB"
	return Image.frombuffer(mode, dimensions, pixels,
				"raw", mode, stride, 1)
	
def findExec(execlist):
	import os
	path = os.environ.get("PATH")
	path = path.split(':')
	for x in path:
		for y in execlist:
			if os.path.exists(x + '/' + y):
				return x + '/' + y
	return ''
	
def getOpenWith(ext):
	import os, subprocess
	command = None
	if os.environ.get("APPDATA"):
		try:
			import _winreg
			a = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, ext)
			i = 0
			while 1:
				name, value, type = _winreg.EnumValue(a, i)
				if name == '':
					ftype = value
					break
				i = i + 1
			a = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, ftype + '\\\\shell\\open\\command')
			name, value, type = _winreg.EnumValue(a, 0)
			execc = value.split('"')[1::2]
			command = value.replace(execc[0], "")
			command = command.split()
			command.pop(0)
			command.pop(command.index('"%L"'))
			command.insert(0, execc[0])
		except:
			# try to find a way to open some of most popular media files
			programfiles = os.environ.get("ProgramFiles")
			command = programfiles + '\\Windows Media Player\\wmplayer.exe'
			command = command.split()
	else:
		try:
			import mimetypes, os
			mimetypes.init()
			mime = mimetypes.types_map[ext]
			c = 'xdg-mime query default ' + mime
			c = c.split()
			result = subprocess.Popen(c, stdout=subprocess.PIPE)
			result.wait()
			result = result.stdout.read()
			fh = open('/usr/share/applications/'+result[:-1])
			for x in fh.readlines():
				if x.startswith('Exec'):
					g = x.split('=')
					command = g[1][:-1]
					command = command.split()
					if "%U" in command:
						command.pop(command.index("%U"))
		except Exception, e:
			# try to find a way to open some of most popular media files
			command = '/usr/bin/firefox'
			if (ext == '.mp3'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'juk', 'totem', 'clementine'])
			if (ext == '.aac'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'juk', 'totem', 'clementine'])
			if (ext == '.ogg'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'juk', 'totem', 'clementine'])
			if (ext == '.mp4'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'dragon', 'totem', 'clementine'])
			if (ext == '.avi'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'dragon', 'totem', 'clementine'])
			if (ext == '.mpg'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'dragon', 'totem', 'clementine'])
			if (ext == '.ogv'):
				command = findExec(['smplayer', 'umplayer', 'vlc', 'dragon', 'totem', 'clementine'])
			command = command.split()
	return command

def guess_de():
	import os
	try:
		known_de = ['xfce', 'gnome', 'ubuntu', 'mate', 'kde', 'cinnamon']
		if os.environ.has_key('DESKTOP_SESSION'):
			desktop_session = os.environ['DESKTOP_SESSION']
		else:
			desktop_session = 'default'

		if desktop_session in known_de:
			return desktop_session
		else:
			if os.environ.has_key('KDE_FULL_SESSION') and os.environ['KDE_FULL_SESSION']:
				return 'kde'
			if os.environ.has_key('MATECORBA_SOCKETDIR') and os.environ['MATECORBA_SOCKETDIR']:
				return 'mate'
		return None
	except:
		return None

def strip_win32_incompat(string, BAD = '\:*?;"<>|/'):
	import re, os
	"""Strip Win32-incompatible characters.
	This only works correctly on Unicode strings.
	"""
	string = unicode(string,'latin-1')
	new = u"".join(map(lambda s: (s in BAD and "_") or s, string))
	parts = new.split(os.sep)
	def fix_end(string):
		return re.sub(r'[\. ]$', "_", string) 
	return unicode(os.sep).join(map(fix_end, parts))
	
def search_iter(model, c, value):
	try:
		iter = model.get_iter_root()
		while (iter):
			if value == model[iter][c]:
				return iter
			iter = model.iter_next(iter)
		return None
	except:
		return None
		
def msg_info(message):
	import gtk
	message = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
	message.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
	message.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
	resp = message.run()
	message.destroy()
	return resp

def msg_error(message):
	import gtk
	message = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_NONE, message)
	message.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
	message.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
	resp = message.run()
	message.destroy()
	return resp

def msg_question(message):
	import gtk
	message = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, message)
	message.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
	message.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
	resp = message.run()
	message.destroy()
	return resp
	
def msg_warning(message):
	import gtk
	message = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE, message)
	message.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
	message.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
	resp = message.run()
	message.destroy()
	return resp
