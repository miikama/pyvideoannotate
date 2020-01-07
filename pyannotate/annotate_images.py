

import cv2
import tkinter 
import math
import time
import logging

from pyannotate.annotation_holder import ImageAnnotations
from PIL import Image, ImageTk


# load logger
logger = logging.getLogger("AnnotationWidget")



class UpdateLabel(tkinter.Label):


    def __init__(self, parent, text, update_field_name, image_annotations ):
        """
            update_field_name is a string of the property field in 
            image_annotations related to this updatelabel
        """

        self.descript_text = text  
        self.annotator = image_annotations
        self.field_name = update_field_name
        try:
            full_text = self.get_updated_text()      
        except AttributeError:
            raise AttributeError("VideoAnnotations class does not have a property field '{}'.".format(update_field_name))

        super().__init__(parent, text=full_text)

    def get_updated_text(self):
        obj = getattr(self.annotator.__class__, self.field_name)
        new_text = "{}".format(obj.__get__(self.annotator, self.annotator.__class__))
        return "{}: {}".format(self.descript_text, new_text)

    def update_text(self):
        new_text = self.get_updated_text()
        self.configure(text=new_text)
        self.text = new_text


class AnnotationWidget(tkinter.Tk):


    def __init__(self, image_annotations):

        """
            Give a VideoAnnotations object as argument
        """

        self.annotator = image_annotations

        # A root window for displaying objects
        super().__init__()

        # keep track how many elements are added to the main grid
        self._main_grid_rows = 0
        self._drawing = False        
        self._original_click_pos = (0,0)

        ################################## header ##################################

         # Header info labels
        self.info_parent = tkinter.Label(self)
        self.info_parent.pack(fill=tkinter.X, pady=5, padx=20)        
        
        
        self.info_labels = [UpdateLabel(self.info_parent, 'Class: ', 'active_annotation_class', self.annotator),
                            UpdateLabel(self.info_parent, 'Object id: ', 'active_annotation_object_id', self.annotator),
                            UpdateLabel(self.info_parent, 'Image count', 'frame_count', self.annotator),
                            UpdateLabel(self.info_parent, 'Current Image', 'current_frame', self.annotator)]

        for ind, label in enumerate(self.info_labels):
            label.pack(side=tkinter.LEFT, padx=5)

        ################################## class and object optionmenus  ##################################

        self.menu_parent = tkinter.Label(self)

        # add an active annotation class widget
        self.class_string = tkinter.StringVar()
        self.class_string.set(self.annotator.active_annotation_class)
        self.annotator_select_widget = tkinter.OptionMenu(self.menu_parent, self.class_string, *self.annotator.annotation_classes, command=self.annotator_class_selection_callback)
        self.annotator_select_widget.pack(side=tkinter.LEFT, padx=10)
        self.annotator_select_widget.config(width=40)

        # add an active annotation object widget
        self.obj_string = tkinter.IntVar()
        self.obj_string.set(self.annotator.active_annotation_object_id)
        logger.debug(f"current_frame_objects: {self.annotator.current_frame_object_ids}")        
        self.annotator_obj_select_widget = tkinter.OptionMenu(self.menu_parent, self.obj_string, *self.annotator.current_frame_object_ids, command=self.annotator_object_selection_callback)
        self.annotator_obj_select_widget.pack(side=tkinter.LEFT, padx=10)
        self.annotator_obj_select_widget.config(width=20)

        self.menu_parent.pack(fill=tkinter.X)


        ################################## image ##################################

        # Video viewing frame
        self.image_area = tkinter.Canvas(self)
        self.image_area.pack(fill=tkinter.X)




        ################################## footer ##################################


        # buttons
        self.button_parent = tkinter.Label(self)
        self.button_parent.pack(fill=tkinter.X, pady=5, padx=20)

        self.buttons = [tkinter.Button(self.button_parent, text="Next frame", command=self.next_frame),
                        tkinter.Button(self.button_parent, text="Previous frame", command=self.prev_frame),                                                
                        tkinter.Button(self.button_parent, text="Mark annotations", command=self.mark_annotation),
                        tkinter.Button(self.button_parent, text="Save annotations", command=self.save_annotations)]



        # order buttons 
        for ind, but in enumerate(self.buttons):
            but.pack(side=tkinter.LEFT, padx=5)

        self._current_frame = self.annotator.read_new_frame()
        self.on_gui_update()

        # bind events 
        self.bind_events()

        # Start the GUI
        self.mainloop() 


    class update_gui:
        """ Creating a class for wrapping gui updates in a decorator """
        def __init__(self, func, *args, **kwargs):
            self._func = func

        def __get__(self, instance, owner):
            """
                Instance is the AnnotationWidget object
                owner is the AnnotationWidget class
             """
            self.cls = owner
            self.obj = instance
            return self.__call__

        def __call__(self, *args, **kwargs):                  
            self._func(self.obj, *args, **kwargs)
            self.obj.on_gui_update()        
            

    def bind_events(self):

        # listen to mouse clicks on canvas
        self.image_area.bind('<Button-1>', self.image_area_clicked)
        self.image_area.bind('<B1-Motion>', self.image_area_dragged)
        self.image_area.bind('<ButtonRelease-1>', self.image_area_released)

        def delegate_key_presses(event):

            # start annotation by m    
            if event.char == 'm':
                self.mark_annotation()
            elif event.char == "c":
                self.next_annotation_class()
            elif event.char == "v":
                self.next_annotation_object()
            elif event.char == "a":
                self.prev_frame()
            elif event.char == "d":
                self.next_frame()
            elif event.char == "q":
                self.quit()
        
        # tkinter only allows binding general key pressed, use an inner function to do the work
        self.bind('<Key>', delegate_key_presses)                



    def update_frame(self):

        if self._current_frame is None:
            raise RuntimeError("should always have frame")

        # copied frame
        frame_copy = self._current_frame.copy()

        # draw the detections 
        self.draw_detections(frame_copy)

        # Convert the Image object into a TkPhoto object
        image = Image.fromarray(frame_copy)
        self.curr_frame = ImageTk.PhotoImage(image=image) 
       
        image_ref = self.image_area.create_image((0,0,), anchor=tkinter.NW, image=self.curr_frame)
        self.image_area.tag_lower(image_ref)

        height, width, clrs = frame_copy.shape
        self.image_area.config(width=width, height=height)

        


    def on_gui_update(self):
        """
            update everything that needs updating
        """
        for label in self.info_labels:
            label.update_text()

        self.class_string.set(self.annotator.active_annotation_class)
        self.obj_string.set(self.annotator.active_annotation_object_id)

        # update the possible available frame objects
        self.update_menu_options(self.annotator_obj_select_widget,
                                 self.annotator.current_frame_object_ids,
                                 self.annotator_object_selection_callback)  

        self.update_frame()

    def draw_detections(self, frame):

        # get the annotations for this frame
        annotations = self.annotator.get_frame_annotations()
        active_annotation = self.annotator.active_annotation_object

        for annotation in annotations:    
            annotation.update_annotation(visible=True)        
            active = annotation.obj_id == active_annotation.obj_id
            print(f"annotation obj_id {annotation.obj_id}, active obj id: {active_annotation.obj_id}")
            print(f"annotation {annotation} is active {active}")
            annotation.draw_annotation_to_array(frame,
                                       self.annotator.get_class_color(annotation.class_name), active)

    def update_menu_options(self, optionmenu, new_options, command):
        """
            Update the shown options for the argument optionmenu.
            Also needs a reference to the function to be called 
            when the new options are selected.
        """
        menu = optionmenu['menu']

        # delete previous values
        menu.delete(0, "end")

        # add new options
        for option in new_options:
            menu.add_command(label=option, command=command)

    def image_area_clicked(self, event):
        self._original_click_pos = (event.x, event.y)
        self._drawing = True

    @update_gui
    def image_area_dragged(self, event):
        """
            redraw the active bbox as dragging
            bboxes are found through their tag (which is their class_name)
        """
        # if tag is just a number string, tkinter mixes it with id :/
        active_annotation_object = self.annotator.active_annotation_object

        # update annotation
        if active_annotation_object is not None:                            
            self.annotator.update_annotation((*self._original_click_pos, event.x, event.y))

    @update_gui
    def image_area_released(self, event):
        if self._drawing:
            self._drawing = False

    @update_gui
    def mark_annotation(self):
        self.annotator.add_annotation()        
        self._drawing = True
        print("starting annotation marking")   

    @update_gui
    def annotator_object_selection_callback(self, object_id):
        """callback gets the new selected option as argument"""   
        print(f"updating active_object with object_id: {object_id} and type {type(object_id)}")     
        self.annotator.active_annotation_object = object_id 

    @update_gui
    def annotator_class_selection_callback(self, active_name):
        """callback gets the new selected option as argument"""                
        self.annotator.active_annotation_class = active_name 

    @update_gui
    def next_annotation_class(self):
        self.annotator.next_annotation_class()

    @update_gui
    def next_annotation_object(self):
        self.annotator.next_annotation_object_in_current_frame()

    @update_gui
    def next_frame(self):        
        self._current_frame = self.annotator.get_next_frame()        

    @update_gui
    def prev_frame(self):        
        self._current_frame = self.annotator.get_prev_frame()        

    @update_gui
    def save_annotations(self):
        self.annotator.save_annotations()

    @update_gui
    def increase_skip_frames(self):
        self.annotator.frame_skip_count = max(self.annotator.frame_skip_count * 2,1)

    @update_gui
    def decrease_skip_frames(self):
        self.annotator.frame_skip_count = math.floor(self.annotator.frame_skip_count / 2)        

    @property
    def root_row_index(self):
        self._main_grid_rows += 1
        return self._main_grid_rows -1    
    







if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    import argparse

	
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--image_folder', type=str, required=True,
        help='path to input image folder'
    )

    parser.add_argument(
        '--annotation_out', type=str,
        help='path to output annotations, default '
    )

    parser.add_argument(
        '--class_file', type=str,
        help='path to annotation classes file, class names on separate rows'
    )

    parser.add_argument(
        '--annotation_file', type=str,
        help='path to json file with already annotated frames, see example_json.json.'
    )

    args = parser.parse_args()

    vann = ImageAnnotations(args.image_folder, args.annotation_out, args.class_file, args.annotation_file)

    AnnotationWidget(vann)

