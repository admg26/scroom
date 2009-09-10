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
        self.text = []
        self.output_text = ""
        self.scroll = 0
        self.current_point = [20,20]

    # Handle the expose-event by drawing
    def do_expose_event(self, widget, event):
        """Sets up cairo and calls draw() to draw the text"""

        # Create the cairo context
        self.cr = self.window.cairo_create()
       
        #Create a pango layout
        self.pg = self.cr.create_layout()

         # Restrict Cairo to the exposed area; avoid extra work
        self.cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        self.cr.clip()

        self.draw(*self.window.get_size())

    def parse_text(self):
        """Decides what section of text needs to be shown"""
 
        line_count  = range(len(self.text))
        
        lines_to_show = 100
        if line_count < 100:
            lines_to_show = line_count 
        
        self.output_text = '\n'.join(self.text[0:170]) 

    def draw(self, width, height):
        """Invokes cairo and pango to draw the text"""

        #self.cr.move_to(20, self.current_point[1]+self.scroll)
        self.cr.move_to(20, 20)

        #pango.SCALE = 1000
        #Set the Pango fonti
        font_size = 10 + self.scroll
        desc = pango.FontDescription("sans normal %s" % font_size)
        self.pg.set_font_description(desc)
        self.parse_text()
        self.pg.set_text(self.output_text)
        #print self.pg.get_pixel_extents()
        #print "line count " + str(self.pg.get_line_count())
        #print "pixel size " + str(self.pg.get_pixel_size())
        #print pango.SCALE
        #Render text with Cairo
        self.cr.show_layout(self.pg)
        #cr.set_font_size(10)
        #cr.move_to(20,21)
        #cr.show_text("test")

    def redraw_canvas(self,scroll):
        """Invalidates the cairo area and 
        updates the pango layout when text
        needs to be redrawn"""

        self.scroll = scroll

        self.current_point = list(self.cr.get_current_point())

        if self.window:
            x, y, w, h = self.get_allocation()
            self.window.invalidate_rect((0,0,w,h), False)
            self.cr = self.window.cairo_create()
            self.cr.update_layout(self.pg)

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
        """Set up the window, events and the UIManager"""
        
        __gsignals__ = { "expose-event": "override" }

        self.filename = ""
        # Create a top level window
        self.window = gtk.Window()
        
        #self.window.add_events(gtk.gdk.SCROLL_MASK)
        #self.window.connect("scroll-event", self.do_scroll)
        
        self.scroll_distance = 0
        self.last_mouse_value = []
        self.window.connect('drag_motion', self.do_drag)
        self.window.connect('drag_end', self.do_stop_drag)

        self.window.drag_dest_set(gtk.DEST_DEFAULT_MOTION,
                                [("", gtk.TARGET_SAME_APP, 1)],
                                gtk.gdk.ACTION_PRIVATE)
        self.window.drag_source_set(gtk.gdk.BUTTON1_MASK,
                                [("", gtk.TARGET_SAME_APP, 1)],
                                gtk.gdk.ACTION_PRIVATE)


        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.window.set_default_size(600, 500)
        self.window.move(300,300)

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

    def do_drag(self, widget, context, x, y, t):
        """Handles the drag event. Causes the
        canvas to be redrawn"""
        
        if self.last_mouse_value:
            dy = self.last_mouse_value[0] - y  
            dt = self.last_mouse_value[1] - t  
            self.last_mouse_value = [y,t]

            self.drawing.redraw_canvas(dy*2)
        else:
            self.last_mouse_value = [y,t]
            self.drawing.redraw_canvas(0)
        return False
        
    def do_stop_drag(self, widget, context):
        """Resets the mouse y and t values so they can be re-assigned
        at the start of the next drag"""
        self.last_mouse_value = []


    """
    def do_scroll(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            print "Scroll up"
            self.scroll_distance = -1
            self.drawing.redraw_canvas(self.scroll_distance)
        else:
            print "Scroll down"
            self.scroll_distance = 1
            self.drawing.redraw_canvas(self.scroll_distance)
    """

    def quit_viewer(self,data=None):
        """Quits program"""
        
        gtk.main_quit()
    
    def open_file(self, widget, data=None):
        """Opens a file chooser dialog and returns the filename.
        Canvas is redrawn if a valid file is opened"""
        
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
                self.drawing.text = ifile.read().split('\n')
                ifile.close()
                dialog.destroy()
                self.drawing.redraw_canvas(0)    
            except IOError:
                pass

    
        elif response == gtk.RESPONSE_CANCEL:
            self.window.set_title("Python Viewer")
            dialog.destroy() 



if __name__ == '__main__':
    PyViewer()
    gtk.main()

