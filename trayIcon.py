import gtk
import gobject
import os

use_appind = True
try:
    import appindicator
except:
    use_appind = False


class TrayIcon:
    def __init__(self, tvmaxe):
        self.tvmaxe = tvmaxe
        self.gui = tvmaxe.gui

        if use_appind:
            self.trayIcon = appindicator.Indicator(
                "tv-maxe",
                "distributor-logo",
                appindicator.CATEGORY_OTHER)
            self.trayIcon.set_status(appindicator.STATUS_PASSIVE)
            self.trayIcon.set_label('TV-Maxe')
            self.trayIcon.set_property('title', 'TV-Maxe')
            self.trayIcon.set_property('icon-desc', 'TV-Maxe')
            self.trayIcon.set_icon("{0}/tvmaxe.png".format(os.getcwd()))
            self.trayIcon.set_menu(self.gui.get_object('menu9'))
        else:
            self.trayIcon = gtk.status_icon_new_from_file("tvmaxe.png")
            self.trayIcon.connect('button-press-event', self.pop_up_menu)
        self.trayIcon.connect('scroll-event', self.scroll)

    def show(self):
        if use_appind:
            self.trayIcon.set_status(appindicator.STATUS_ACTIVE)
        else:
            self.trayIcon.set_visible(True)

    def hide(self):
        if use_appind:
            self.trayIcon.set_status(appindicator.STATUS_PASSIVE)
        else:
            self.trayIcon.set_visible(False)

    def toggle(self, obj, event=None):
        if obj.get_active():
            self.show()
        else:
            self.hide()

    def scroll(self, obj, event):
        if event.direction.value_name == 'GDK_SCROLL_DOWN':
            gobject.idle_add(self.tvmaxe.setVolume, None, None, -0.1)
        elif event.direction.value_name == 'GDK_SCROLL_UP':
            gobject.idle_add(self.tvmaxe.setVolume, None, None, 0.1)

    def set_tooltip_text(self, message):
        if use_appind:
            pass
        else:
            self.trayIcon.set_tooltip_text(message)

    def pop_up_menu(self, obj, event):
        if event.button == 1:
            if self.tvmaxe.tvmaxevis:
                if self.tvmaxe.radioMode:
                    self.gui.get_object('window13').hide()
                else:
                    self.gui.get_object('window1').hide()
                self.gui.get_object('menuitem29').set_label(_('Show TV-MAXE'))
                self.tvmaxe.tvmaxevis = False
            else:
                if self.tvmaxe.radioMode:
                    self.gui.get_object('window13').show()
                else:
                    self.gui.get_object('window1').show()
                self.gui.get_object('menuitem29').set_label(_('Hide TV-MAXE'))
                self.tvmaxe.tvmaxevis = True
        if event.button == 3:
            if self.tvmaxe.mediaPlayer.isPlaying():
                self.gui.get_object('menuitem30').set_sensitive(True)
            else:
                self.gui.get_object('menuitem30').set_sensitive(False)
            self.gui.get_object('menu9').popup(
                None,
                None,
                gtk.status_icon_position_menu,
                event.button,
                event.time,
                obj)
