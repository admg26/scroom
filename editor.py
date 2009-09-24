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
        """
            Resets defaults values when new file is opened
        """

        self.text = []
        self.output_text = ""
        self.scroll = 0
        self.speed = 0
        self.zoom = 12
        self.factor = 0

        self.current_point = [20,20]
        self.min_line = 0
        self.indent = 0

        self.set_pc = 1

        self.char_index = []

        self.line_count = 0

        self.min_text = 0
        self.max_text = 50

        self.min_cairo = 20
        self.max_cairo = 20
        self.tab_cairo = 20

    def set_up_pangocairo(self, widget, event):    
   
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

            #self.attr = pango.AttrSize(self.zoom, 0, -1)
            #self.attrlist = pango.AttrList()
            #self.attrlist.insert(self.attr)
            self.set_pc = 0

            #self.pg.set_attributes(self.attrlist)
        

    # Handle the expose-event by drawing
    def do_expose_event(self, widget, event):
        """
            Sets up cairo and calls draw() to draw the text
        """
        print "expose"  
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
        char_min = 0
        char_max = 0
        
        point = self.line_count
       
        while line_number < point:
        
            if self.indentation(self.text[line_number]): 
                self.char_index.append(self.indent)
                self.text[line_number] = self.text[line_number].strip()      
                line_number += 1 

            else:
                #char_max += len('\n'.join(self.text[line_min:line_number]))
                #char_index.append([self.indent, line_min, line_number, char_min, char_max])
                char_max += 1
                char_min = char_max
                line_min = line_number

    def draw(self, width, height):        
        """
            Invokes cairo and pango to draw the text
        """

        line_spacing = 20
       
        print "draw"
        if self.scroll > 20:
            self.factor = self.scroll * 0.1
            #self.factor = 1000  

        elif self.scroll < -20:
            self.factor = abs(self.scroll) * 0.1
        
        else:
            self.factor = 0
    
        output_text = ""

        if self.text:
            l = self.min_text
            l1 = l
            l2 = l + 1 
            tab_previous = self.char_index[l]

            while l < self.max_text:

                while self.char_index[l + 1] == tab_previous:
                    l2 += 1 
                    l += 1

                self.tab_cairo += tab_previous * 20
                font_size =  int(self.zoom - (tab_previous * self.factor))*pango.SCALE
                
                if font_size < 9000:
                    font_size = 9000
                
                pango.FontDescription.set_size(self.desc, font_size)
                
                self.pg.set_font_description(self.desc)
                line_spacing -= tab_previous * 0.5 

                self.cr.move_to(self.tab_cairo, self.max_cairo)
                
                output_text = '\n'.join(self.text[l1:l2])
                
                self.pg.set_text(output_text)
                self.cr.show_layout(self.pg)


                self.max_cairo += line_spacing * (l2 - l1)             
                self.tab_cairo = 20
                line_spacing  = 20
                l += 1
                tab_previous = self.char_index[l]
                l1 = l
                l2 = l + 1


    def redraw_canvas(self, dy):
        """
            Invalidates the cairo area and updates the 
            pango layout when text needs to be redrawn
        """
        self.scroll = dy/20
        
        print "redraw"

        if self.scroll > 0:
            
            if self.min_cairo < -20:
                self.min_cairo = 0 
                self.min_text += 1 
                self.max_text += 1
                
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

            if self.min_text < 0:
                self.min_cairo = 20
                self.min_text = 0
                self.max_text = 50
                self.scroll = 0
        
           

        self.min_cairo -= self.scroll
        self.max_cairo = self.min_cairo

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
                
        """
            Set up the window, events and the UIManager
        """
        
        __gsignals__ = { "expose-event" : None}

        self.filename = ""
        self.source_id = 0
        self.dy = 0

        # Create a top level window
        self.window = gtk.Window()
        
        
        self.scroll_distance = 0
        self.mouse_click_point = 0
        
        #Create a TextArea class instance
        self.drawing = TextArea()

        self.drawing.show()
        
        self.window.connect('drag_begin', self.start_refresh)
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
        self.current_scale = 16

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
                
                self.drawing.end_count = [(self.drawing.line_count // 100),(self.drawing.line_count % 100)]

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
        
