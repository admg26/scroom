#!/usr/bin/env python

"""
This program attempts to implement an automatic zooming and scrolling tool for viewing
large python files. The principle behind the program is to selectively make sections of
code smaller as the user scrolls down faster whilst leaving the main class and function 
definitions at the same size. Flow of information is faster with this technique conpared 
to scrolling at a constant zooming level. Ideas for this program were based on a paper
written by Igarashi and Hinckley: Speed-dependent Automatic Zooming for Browsing Large Documents, 
CHI letters vol2, 2.

The implementation is done using PyGTK using Cairo for the rendering and Pango for the 
font descriptions.

Author: Alison Ming
Email: adk33@cam.ac.uk
Date: 25th Sept 2009

"""

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
        self.connect("expose-event", self.do_expose_event)
        self.set_initial_values()

    def set_initial_values(self): 
        """
            Resets defaults values when new file is opened
        """
        #Stores each line of the text file in a list
        self.text = []
        
        #Scrolling distance
        self.scroll = 0

        #Zooming level (font size) 
        self.zoom = 12

        #Factor by which is decrement self.zoom
        self.factor = 0

        #Number of tabs spaces before a line
        self.indent = 0

        #Flag to only set up pango descriptions only once 
        self.set_pc = 1

        #list of indetation level of all lines
        self.tab_index = []

        #Total line count
        self.line_count = 0

        #line number of line rendered off top of window 
        self.min_text = 0
        #line number of line rendered off bottom of window 
        self.max_text = 50

        #y position for cairo for the text at the top
        self.min_cairo = 20

        #y position for text at bottom
        self.max_cairo = 20

        #x positiong for indented text
        self.tab_cairo = 20

    def set_up_pangocairo(self, widget, event):    
        """
            Sets up the cairo context and pango layout
        """

        # Create the cairo context
        self.cr = self.window.cairo_create()
         
        #Create a pango layout
        self.pg = self.cr.create_layout()

        # Restrict Cairo to the exposed area; avoid extra work
        self.cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        self.cr.clip()

        if self.set_pc:
            self.desc = pango.FontDescription("sans normal")
            pango.FontDescription.set_size(self.desc, int(self.zoom*1024))
            self.pg.set_font_description(self.desc)

            #Only reset cairo and pango if new file is opened
            self.set_pc = 0

        
    def do_expose_event(self, widget, event):
        """
            Handles expose event.
            Sets up cairo and calls draw() to draw the text
        """

        self.set_up_pangocairo(widget, event)

        self.draw(*self.window.get_size())


    def indentation(self, text):
        """ 
            Decides if the current line is indented to the 
            same number of tabs as the previous one.
            If not, sets self.indent to the current value.
        """

        tab = text.rfind(' '*4)

        if tab != -1:  
            if tab%4 == 0:
                if tab//4 + 1 == self.indent:
                    return True

                else:
                    self.indent = tab//4 + 1
                    return False
            
            else:
                return True

        else:
            return True



    def parse_text(self):
        """
            Builds a list of the indentation level in the text
        """

        line_number = 0
        line_min = 0
        
        while line_number < self.line_count:
        
            if self.indentation(self.text[line_number]): 
                self.tab_index.append(self.indent)
                self.text[line_number] = self.text[line_number].strip()      
                line_number += 1 

            else:
                line_min = line_number


    def draw(self, width, height):        
        """
            Finds chunks of text with the same indentation level
            and renders it as one block
            Invokes cairo and pango to draw the text
        """
        
        line_spacing = 20
       

        #TODO:Smart algorithm to map mouse position to the scrolling speed
        #zooming level should go here
        
        if self.scroll > 20:
            self.factor = self.scroll * 0.1

        elif self.scroll < -20:
            self.factor = abs(self.scroll) * 0.1
            
        elif abs(self.scroll) > 50:
            self.factor =  5
            self.scroll = 50

        else:
            self.factor = 0
    
        output_text = ""

        if self.text:
            l = self.min_text
            l1 = l
            l2 = l + 1
            
            tab_previous = self.tab_index[l]
            
            while l < self.max_text:
                
                #Find all the lines with the same indentation level
                while l < self.line_count - 2 and self.tab_index[l + 1] == tab_previous:
                    l2 += 1 
                    l += 1
                
                self.tab_cairo += tab_previous * 20
                font_size =  int(self.zoom - (tab_previous * self.factor))*pango.SCALE
                
                #Set a minimum font size
                if font_size < 8000:
                    font_size = 8000
                
                pango.FontDescription.set_size(self.desc, font_size)
                self.pg.set_font_description(self.desc)
                
                #Adjust line spacing as font size decreases
                line_spacing -= tab_previous * 0.5 

                self.cr.move_to(self.tab_cairo, self.max_cairo)
                
                output_text = '\n'.join(self.text[l1:l2])
                
                self.pg.set_text(output_text)
                self.cr.show_layout(self.pg)

                self.max_cairo += line_spacing * (l2 - l1)             
                
                #Reset all values
                self.tab_cairo = 20
                line_spacing  = 20
                l += 1
                
                try:
                    tab_previous = self.tab_index[l]
                
                except IndexError:
                    tab_previous = self.tab_index[-1]
                
                l1 = l
                l2 = l + 1


    def redraw_canvas(self, dy):
        """
            Invalidates the cairo area and updates the 
            pango layout when text needs to be redrawn
        """
        self.scroll = dy/20
        
        if self.scroll > 0:
            
            if self.min_cairo < -20:
                self.min_cairo = 0 
                self.min_text += 1 
                self.max_text += 1
     
            #When bottom of document is reached stop scrolling
            if self.max_text > self.line_count + 2:
                self.min_cairo = 0
                self.min_text = self.line_count - 50
                self.max_text = self.line_count
                self.scroll = 0
     
        elif self.scroll < 0:
            if self.min_cairo > 0:
                self.min_cairo = -20
                self.min_text -= 1
                self.max_text -=1

            #Do not scroll up if already at top of document
            if self.min_text < 0:
                self.min_cairo = 20
                self.min_text = 0
                self.max_text = 50
                self.scroll = 0
        
        #Do the scrolling
        self.min_cairo -= self.scroll
       
        self.max_cairo = self.min_cairo
        self.invalidate_canvas()


    def invalidate_canvas(self):
        """
            Invalidates the canvas to allow cairo to redraw
        """

        if self.window:
            x, y, w, h = self.get_allocation()
            self.window.invalidate_rect((0,0,w,h), False)
            self.cr = self.window.cairo_create()
            self.cr.update_layout(self.pg)


class PyViewer():
    #XML description fo Menu bar at the top. Uses UIManager

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
        
        __gsignals__ = { 'expose-event' : 'override'}

        self.filename = ""
        self.source_id = 0
        self.dy = 0

        # Create a top level window
        self.window = gtk.Window()
        
        #Get y position of mouse at start of drag 
        self.mouse_click_point = 0
        
        #Create a TextArea class instance
        self.drawing = TextArea()

        self.drawing.show()
        
        self.window.connect('drag-begin', self.start_refresh)
        self.window.connect('drag-motion', self.drag_motion)
        self.window.connect('drag-end', self.stop_drag_motion)
        
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

        #Create a UIManager instance
        uimanager = gtk.UIManager()
        self.current_scale = 16

        #Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)

        #Create an ActionGroup
        actiongroup = gtk.ActionGroup('PyViewer')
        self.actiongroup = actiongroup
        
        #Create actions
        actiongroup.add_actions([('Open', gtk.STOCK_OPEN, '_Open', None, None, self.open_file),
                                 ('Quit', gtk.STOCK_QUIT, '_Quit', None, None, self.quit_viewer),
                                 ('File', None, '_File')])
       
        #Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        #Add a UI description
        uimanager.add_ui_from_string(self.ui)

        #Create a MenuBar
        menubar = uimanager.get_widget('/MenuBar')
        
        #Pack the menubar and the drawing area into a vbox
        vbox.pack_start(menubar, False)
        vbox.pack_start(self.drawing)   

        self.window.show_all()

        return


    def continuous_scroll(self, context):
        """
            Calls redraw_cavas() and returns True
        """

        self.drawing.redraw_canvas(self.dy)
        
        return True


    def start_refresh(self, widget, context):
        """
            Calls continuous_scroll every 38 ms until drag stops and the gobject.source is removed
        """

        self.source_id = gobject.timeout_add(38, self.continuous_scroll, context)


    def drag_motion(self, widget, context, x, y, t):
        """
            Handles the drag event. Causes the canvas to be redrawn
        """
        
        if self.mouse_click_point:
            self.dy = y - self.mouse_click_point
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

        #Displays a fiel chooser dialog
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
                
                self.drawing.line_count = len(self.drawing.text)
                
                self.drawing.parse_text()

                self.drawing.redraw_canvas(0)    
            except IOError:
                pass
    
        elif response == gtk.RESPONSE_CANCEL:
            self.window.set_title("Python Viewer")
            dialog.destroy() 

if __name__ == '__main__':
    PyViewer()
    gtk.main()
        
