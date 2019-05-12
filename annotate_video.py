

import cv2
import tkinter 
import math
import time
import logging

from annotation_holder import VideoAnnotations
from PIL import Image, ImageTk


# load logger
logger = logging.getLogger("AnnotationWidget")



class UpdateLabel(tkinter.Label):


    def __init__(self, parent, text, update_field_name, video_annotations ):
        """
            update_field_name is a string of the property field in 
            video_annotations related to this updatelabel
        """

        self.descript_text = text  
        self.vann = video_annotations
        self.field_name = update_field_name
        try:
            full_text = self.get_updated_text()      
        except AttributeError:
            raise AttributeError("VideoAnnotations class does not have a property field '{}'.".format(update_field_name))

        super().__init__(parent, text=full_text)

    def get_updated_text(self):
        obj = getattr(self.vann.__class__, self.field_name)
        new_text = "{}".format(obj.__get__(self.vann, self.vann.__class__))
        return "{}: {}".format(self.descript_text, new_text)

    def update_text(self):
        new_text = self.get_updated_text()
        self.configure(text=new_text)
        self.text = new_text


class AnnotationWidget(tkinter.Tk):


    def __init__(self, video_annotations):

        """
            Give a VideoAnnotations object as argument
        """

        self.vann = video_annotations

        # A root window for displaying objects
        super().__init__()

        # keep track how many elements are added to the main grid
        self._main_grid_rows = 0
        self._drawing = False        
        self._original_click_pos = (0,0)

        # for controlling the video playing
        self._video_playing = False
        self._last_frame_change = time.time()

        ################################## header ##################################

         # Header info labels
        self.info_parent = tkinter.Label(self)
        self.info_parent.pack(fill=tkinter.X, pady=5, padx=20)

        
        
        
        self.info_labels = [UpdateLabel(self.info_parent, 'Class: ', 'active_annotation_class', self.vann),
                            UpdateLabel(self.info_parent, 'Object id: ', 'active_annotation_object_id', self.vann),
                            UpdateLabel(self.info_parent, 'Frame count', 'frame_count', self.vann),
                            UpdateLabel(self.info_parent, 'Current frame', 'current_frame', self.vann),
                            UpdateLabel(self.info_parent, 'FPS', 'fps', self.vann),
                            UpdateLabel(self.info_parent, 'Frames to skip', 'frame_skip_count', self.vann),
                            UpdateLabel(self.info_parent, 'Time between frames', 'time_between_frames', self.vann)]


        
        for ind, label in enumerate(self.info_labels):
            label.pack(side=tkinter.LEFT, padx=5)

        ################################## class and object optionmenus  ##################################

        self.menu_parent = tkinter.Label(self)

        # add an active annotation class widget
        self.class_string = tkinter.StringVar()
        self.class_string.set(self.vann.active_annotation_class)
        self.ann_select_widget = tkinter.OptionMenu(self.menu_parent, self.class_string, *self.vann.annotation_classes, command=self.ann_class_selection_callback)
        self.ann_select_widget.pack(side=tkinter.LEFT, padx=10)
        self.ann_select_widget.config(width=40)

        # add an active annotation object widget
        self.obj_string = tkinter.IntVar()
        self.obj_string.set(self.vann.active_annotation_object_id)
        logger.debug(f"current_frame_objects: {self.vann.current_frame_object_ids}")        
        self.ann_obj_select_widget = tkinter.OptionMenu(self.menu_parent, self.obj_string, *self.vann.current_frame_object_ids, command=self.ann_object_selection_callback)
        self.ann_obj_select_widget.pack(side=tkinter.LEFT, padx=10)
        self.ann_obj_select_widget.config(width=20)

        self.menu_parent.pack(fill=tkinter.X)


        ################################## image ##################################

        # Video viewing frame
        self.image_area = tkinter.Canvas(self)
        self.image_area.pack(fill=tkinter.X)




        ################################## footer ##################################


        # buttons
        self.button_parent = tkinter.Label(self)
        self.button_parent.pack(fill=tkinter.X, pady=5, padx=20)

        self.buttons = [tkinter.Button(self.button_parent, text="Play", command=self.play_video),
                        tkinter.Button(self.button_parent, text="Pause", command=self.pause_video),
                        tkinter.Button(self.button_parent, text="Next frame", command=self.next_frame),
                        tkinter.Button(self.button_parent, text="Previous frame", command=self.prev_frame),                        
                        tkinter.Button(self.button_parent, text="Increase skipped frames", command=self.increase_skip_frames),
                        tkinter.Button(self.button_parent, text="Decrease skipped frames", command=self.decrease_skip_frames),
                        tkinter.Button(self.button_parent, text="Mark annotations", command=self.mark_annotation),
                        tkinter.Button(self.button_parent, text="Save annotations", command=self.save_annotations)]



        # order buttons 
        for ind, but in enumerate(self.buttons):
            but.pack(side=tkinter.LEFT, padx=5)

        frame = self.vann.read_new_frame()
        self.update_frame(frame)

        # bind events 
        self.bind_events()

        # ready to play the video
        self.play_video_loop()

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

        # play video
        self.bind('<space>', self.toggle_play)

        def delegate_key_presses(event):

            # start annotation by m    
            if event.char == 'm':
                self.mark_annotation()
            elif event.char == "c":
                self.next_annotation()
        
        # tkinter only allows binding general key pressed, use an inner function to do the work
        self.bind('<Key>', delegate_key_presses)                



    def update_frame(self, new_frame):

        # Convert the Image object into a TkPhoto object
        image = Image.fromarray(new_frame)
        self.curr_frame = ImageTk.PhotoImage(image=image) 
       
        image_ref = self.image_area.create_image((0,0,), anchor=tkinter.NW, image=self.curr_frame)
        self.image_area.tag_lower(image_ref)

        height, width, clrs = new_frame.shape
        self.image_area.config(width=width, height=height)

        # draw the detections 
        self.draw_detections()


    def on_gui_update(self):
        """
            update everything that needs updating
        """
        for label in self.info_labels:
            label.update_text()

        self.class_string.set(self.vann.active_annotation_class)
        self.obj_string.set(self.vann.active_annotation_object_id)

        # update the possible available frame objects
        self.update_menu_options(self.ann_obj_select_widget,
                                 self.vann.current_frame_object_ids,
                                 self.ann_object_selection_callback)        

        self.draw_detections()

    def draw_detections(self):

        # get the annotations for this frame
        annotations = self.vann.get_frame_annotations()

        for annotation in annotations:            
            annotation.draw_annotation(self.image_area,
                                       self.vann.get_class_color(annotation.class_name))

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



    

    def play_video_loop(self):
        if self._video_playing:
            self.next_frame()
        
        # how long should we wait based on the fps
        target_wait_time = self.vann.time_between_frames
        # how long has it actually been from the latest frame change
        actual_wait = time.time() - self._last_frame_change                

        # TODO: make this better
        # slowly correct towards more appropriate wait time
        correction = .2
        # store the last frame change
        self._last_frame_change = time.time()

        # schedule fps based update in ms
        self.after(int(correction*self.vann.time_between_frames*1000), self.play_video_loop)

    def toggle_play(self, event):
        self._video_playing = not self._video_playing

    def play_video(self):
        self._video_playing = True

    def pause_video(self):
        self._video_playing = False


    def image_area_clicked(self, event):

        self._original_click_pos = (event.x, event.y)

    @update_gui
    def image_area_dragged(self, event):
        """
            redraw the active bbox as dragging
            bboxes are found through their tag (which is their class_name)
        """

        if self._drawing:                        
            # if tag is just a number string, tkinter mixes it with id :/
            active_annotation_object = self.vann.active_annotation_object

            logger.debug(f"active annotation {active_annotation_object}")
            logger.debug(f"current frame objects {self.vann.current_frame_object_ids}")
            
            # add new annotation object
            if active_annotation_object is None:

                self.vann.add_annotation(self.image_area, (*self._original_click_pos, event.x, event.y))

            else:
                self.vann.update_annotation(self.image_area, points=(*self._original_click_pos, event.x, event.y))

    @update_gui
    def image_area_released(self, event):

        if self._drawing:
            self._drawing = False


    @update_gui
    def mark_annotation(self):
        self._drawing = True
        logger.debug("starting annotation marking")   

    @update_gui
    def ann_object_selection_callback(self, object_id):
        """callback gets the new selected option as argument"""   
        logger.debug(f"updating active_object with object_id: {object_id} and type {type(object_id)}")     
        self.vann.active_annotation_object = object_id 

    @update_gui
    def ann_class_selection_callback(self, active_name):
        """callback gets the new selected option as argument"""                
        self.vann.active_annotation_class = active_name 

    @update_gui
    def next_annotation(self):
        self.vann.next_annotation_class()

    @update_gui
    def next_frame(self):
        frame = self.vann.get_next_frame()
        self.update_frame(frame)

    @update_gui
    def prev_frame(self):
        frame = self.vann.get_prev_frame()
        self.update_frame(frame)

    @update_gui
    def save_annotations(self):
        self.vann.save_annotations()

    @update_gui
    def increase_skip_frames(self):
        self.vann.frame_skip_count = max(self.vann.frame_skip_count * 2,1)

    @update_gui
    def decrease_skip_frames(self):
        self.vann.frame_skip_count = math.floor(self.vann.frame_skip_count / 2)        

    @property
    def root_row_index(self):
        self._main_grid_rows += 1
        return self._main_grid_rows -1    
    







if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    import argparse

	
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-v', '--video', type=str, required=True,
        help='path to video file'
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

    vann = VideoAnnotations(args.video, args.annotation_out, args.class_file, args.annotation_file)

    AnnotationWidget(vann)

