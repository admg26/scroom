#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk, gobject
import cairo
import pango


class TextArea(gtk.DrawingArea):
   
    def __init__(self):
		super(TextArea, self).__init__()
		self.connect("expose_event", self.do_expose_event)
		self.text = ""
    # Handle the expose-event by drawing
    def do_expose_event(self, widget, event):
        # Create the cairo context
        cr = self.window.cairo_create()
       
        #Create a pango layout
        self.pg = cr.create_layout()

		 # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())

    def draw(self, cr, width, height):
        cr.move_to(20,20)

        #Set the Pango font
        desc = pango.FontDescription("sans normal 12")
        self.pg.set_font_description(desc)
        self.pg.set_text(self.text)
        
        #Render text with Cairo
        cr.show_layout(self.pg)
        
    def redraw_canvas(self):   
        if self.window:
            x, y, w, h = self.get_allocation()
            self.window.invalidate_rect((0,0,w,h), False)
            cr = self.window.cairo_create()
            cr.update_layout(self.pg)
            self.draw(cr, *self.window.get_size())

class PyViewer():
    ui = '''<ui>
    <menubar name="MenuBar">
      <menu name="File" action="File">
	<menuitem name="Open" action="Open"/>	
        <menuitem name="Quit" action="Quit"/>
      </menu>
    </menubar>

    </ui>'''		
    
    def __init__(self):
		__gsignals__ = { "expose-event": "override" }

		self.filename = ""
		# Create a top level window
		self.window = gtk.Window()
		
		self.window.add_events(gtk.gdk.SCROLL_MASK)
		self.window.connect("scroll-event", self.wakeup)

		self.window.connect('destroy', lambda w: gtk.main_quit())
		self.window.set_size_request(600, 500)

		#Create a TextArea class instance
		self.drawing = TextArea()

		self.drawing.show()
			
		vbox = gtk.VBox()
		self.window.add(vbox)

		# Create a UIManager instance
		uimanager = gtk.UIManager()

		# Add the accelerator group to the toplevel window
		accelgroup = uimanager.get_accel_group()
		self.window.add_accel_group(accelgroup)

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('PyViewer')
		self.actiongroup = actiongroup
		# Create actions
		actiongroup.add_actions([('Open', gtk.STOCK_OPEN, '_Open', None, None, self.open_file),
				 ('Quit', gtk.STOCK_QUIT, '_Quit', None, None, self.quit_viewer),
                                 ('File', None, '_File')])
       
		#actiongroup.get_action('Quit').connect('activate',self.quit_viewer)
        #actiongroup.get_action('Quit').set_property('short-label', '_Quit')
		#actiongroup.get_action('Open').set_property('short-label', '_Open')

        # Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
		uimanager.add_ui_from_string(self.ui)

        # Create a MenuBar
		menubar = uimanager.get_widget('/MenuBar')
		vbox.pack_start(menubar, False)
 	
		vbox.pack_start(self.drawing)	

		self.window.show_all()
		return

    def wakeup(self, widget, event):
		if event.direction == gtk.gdk.SCROLL_UP:
			print "Scroll up"
		else:
			print "Scroll down"

    def quit_viewer(self,data=None):
		gtk.main_quit()
	
    def open_file(self, widget, data=None):
		dialog = gtk.FileChooserDialog("Open..",
                       None,
                       gtk.FILE_CHOOSER_ACTION_OPEN,
                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.filename = dialog.get_filename()	
			self.window.set_title("Python Viewer - " + self.filename )

			try: 
				ifile = open(self.filename, 'r')
				text = ifile.read()
				self.drawing.text = text
				self.drawing.redraw_canvas()	
				ifile.close()
			except IOError:
				pass

			dialog.destroy()
	
		elif response == gtk.RESPONSE_CANCEL:
			self.window.set_title("Python Viewer")
			dialog.destroy() 



if __name__ == '__main__':
	PyViewer()
	gtk.main()

