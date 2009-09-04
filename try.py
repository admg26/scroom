#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gobject
import pango
import gtk
import math
import time
import cairo

TEXT ='cairo'
class PyGtkWidget(gtk.EventBox):
    __gtype_name__ = "PyGtkWidget"

    def __init__(self):
        gtk.Widget.__init__(self)

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)


    def _expose_cairo(self, event, cr, pg):
        cr.move_to(20,20)
        desc = pango.FontDescription("sans bold 16")
        pg.set_font_description(desc)
        pg.set_text("asdasda")
        cr.show_layout(pg)
    def do_expose_event(self, event):
        self.chain(event)
        cr = self.window.cairo_create()
        pg = cr.create_layout()
        #pc = self.create_pango_context()
        self._expose_cairo(event,cr,pg)
win = gtk.Window()
win.set_title('clock')
win.connect('delete-event', gtk.main_quit)

win.set_decorated(True)

w = PyGtkWidget()
win.add(w)

win.move(500, 500)
win.show_all()

gtk.main()   
