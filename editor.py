#!/usr/bin/env python

from __future__ import division
import pygtk
pygtk.require('2.0')
import gtk, gobject
import cairo
import pango
import time

class TextArea(gtk.DrawingArea):
   
    def __init__(self):
        super(TextArea, self).__init__()
        self.connect("expose_event", self.do_expose_event)
        self.set_initial_values()

    def set_initial_values(self):   
        self.text = []
        #self.text = ""
        self.output_text = ""
        self.scroll = 0
        self.speed = 0
        self.zoom = 12
        self.current_point = [20,20]
        self.current_scale = 12
        self.min_line = 100

    # Handle the expose-event by drawing
    def do_expose_event(self, widget, event):
        """
            Sets up cairo and calls draw() to draw the text
        """

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
        """
            Decides what section of text needs to be shown
        """
 
        #line_count  = range(len(self.text))
        
        #lines_to_show = 100
        #if line_count < 100:
        #    lines_to_show = line_count 
        
        self.output_text = '\n'.join(self.text[self.min_line:(self.min_line + 100)]) 

    def draw(self, width, height):        
        """
            Invokes cairo and pango to draw the text
        """
        
        self.cr.move_to(20, self.current_point[1] + self.scroll)
        desc = pango.FontDescription("sans normal")
        print self.cr.get_current_point()

        pango.FontDescription.set_size(desc, int(1024*self.zoom))
        
        self.pg.set_font_description(desc)
        
        self.parse_text()
        self.pg.set_text(self.output_text)
        #self.pg.set_text(self.text)
        
        
        self.cr.show_layout(self.pg)

    def redraw_canvas(self, dy):
        """
            Invalidates the cairo area and updates the 
            pango layout when text needs to be redrawn
        """
        self.scroll = dy/20
        if dy >= 0:
            sign = 1
        else:
            sign = -1

        """
        if abs(dy) > 100 and abs(dy) < 350:
            self.zoom =12 - pow(4,(abs(dy) - 100) / (350 - 100))
            self.scroll = sign * 12 * 12 / self.zoom

        elif abs(dy) <= 100:
            self.zoom = 12
            self.scroll = dy * 12 / 100 

        else:
            self.zoom = 8
            self.scroll = sign * 18
        """

        self.current_point = list(self.cr.get_current_point())

        pango_end_of_text = self.pg.get_pixel_extents()
        window_size = self.window.get_size()


        if self.window:
            x, y, w, h = self.get_allocation()
            self.window.invalidate_rect((0,0,w,h), False)
            self.cr = self.window.cairo_create()
            self.cr.update_layout(self.pg)

        print pango_end_of_text[1][3] - self.current_point[1] # window_size[1]
        
        
        if self.current_point[1] + pango_end_of_text[1][3] < window_size[1] + 92:
            print "true"
            self.min_line += 50
            self.parse_text()
            self.current_point = [20,20]
            self.scroll = 0
        


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
        """
            Set up the window, events and the UIManager
        """
        
        __gsignals__ = { "expose-event": None }

        self.filename = ""
        self.source_id = 0
        self.dy = 0

        # Create a top level window
        self.window = gtk.Window()
        
        
        self.scroll_distance = 0
        self.mouse_click_point = 0

        self.window.connect('drag-begin', self.start_refresh)
        self.window.connect('drag_motion', self.drag_motion)
        self.window.connect('drag_end', self.stop_drag_motion)
    
        self.window.drag_source_set(gtk.gdk.BUTTON1_MASK,
                                [("", gtk.TARGET_SAME_APP, 1)],
                                gtk.gdk.ACTION_PRIVATE)

        self.window.drag_dest_set(gtk.DEST_DEFAULT_MOTION,
                                [("", gtk.TARGET_SAME_APP, 1)],
                                gtk.gdk.ACTION_PRIVATE)
     
        self.window.connect('destroy', lambda w: gtk.main_quit())
    
        self.window.set_default_size(600,900)
        self.window.move(300,100)

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


    def continuous_scroll(self, context):
     
        self.drawing.redraw_canvas(self.dy)
        
        return True

    def start_refresh(self, widget, context):
        self.source_id = gobject.timeout_add(38, self.continuous_scroll, context)


    def drag_motion(self, widget, context, x, y, t):
        """
            Handles the drag event. Causes the canvas to be redrawn
        """
        
        if self.mouse_click_point:
            self.dy = self.mouse_click_point - y
        else:
            self.mouse_click_point = y


    def stop_drag_motion(self, widget, context):
        """
            Resets the mouse y and t values so they can be re-assigned
            at the start of the next drag
        """
        gobject.source_remove(self.source_id)
        self.mouse_click_point = 0

    
    def quit_viewer(self,data=None):
        """
            Quits program
        """
        
        gtk.main_quit()
    


    def open_file(self, widget, data=None):
        """
            Opens a file chooser dialog and returns the filename.
            Canvas is redrawn if a valid file is opened
        """
        
        dialog = gtk.FileChooserDialog("Open..",None,
                       gtk.FILE_CHOOSER_ACTION_OPEN,
                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        response = dialog.run()
        self.drawing.set_initial_values()
        self.drawing.cr.move_to(20,20)

        if response == gtk.RESPONSE_OK:
            self.filename = dialog.get_filename()   
            self.window.set_title("Python Viewer - " + self.filename )

            try: 
                ifile = open(self.filename, 'r')
                self.drawing.text = ifile.read().split('\n')
                #self.drawing.text = ifile.read()
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

