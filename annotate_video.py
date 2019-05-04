

import cv2
import tkinter 
import math
import colorsys
import time

from PIL import Image, ImageTk
from annotation_loader import AnnotationLoader

class VideoAnnotation:

    def __init__(self, start_index):

        self.start = start_index
        self.end = -1



class VideoAnnotations:

    _frames = []

    _cur_index = 0

    # list of tuples (start_index, end_index) that mark the video sequence 
    _sequences = []

    _defaults = {
        'annotation_frame_rate': 5,
        'output_file': 'annotations.txt',
        'annotation_classes': ["class1", "class2"]
    }

    def __init__(self, annotation_vid, output_file, annotation_class_file=None, annotation_file=None):

        # set up default values
        self.__dict__.update(self._defaults) 

        self.output_file = output_file if output_file is not None else self.output_file

        # load class names from file or use defaults if no file given
        self.annotation_classes = self.load_class_names(self.annotation_classes, annotation_class_file)        

        # dictionary of class name -> color
        self.class_colors = self.get_class_colors()

        # dictionary of class name -> class_id 
        self.class_ids =  self.get_class_ids()

        self.cap = self.open_video(annotation_vid)

        # init an annotation loader 
        self.annotation_loader = AnnotationLoader()

        self.frame_annotations = self.load_saved_annotations(self.annotation_loader, annotation_file)

        # number of frames to skip in the next/previous frame call
        self._frame_skip_count = 0

        # which annotation we are going at
        self._active_annotation_index = 0




    

    def open_video(self, video_file):

        cap = cv2.VideoCapture(video_file)

        if not cap.isOpened():
            raise IOError("Couldn't open webcam or video")

        return cap

    def get_next_frame(self):

        self._cur_index = min(self._cur_index + 1 + self.frame_skip_count, self.frame_count-1)

        return self.read_new_frame()


    def read_new_frame(self):

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._cur_index)

        retval, frame = self.cap.read()        

        #Rearrange the color channel
        frame = frame[:,:,::-1]
        
        return frame


    def get_prev_frame(self):

        self._cur_index = max(self._cur_index -1 - self.frame_skip_count, 0)

        return self.read_new_frame()

    def mark_sequence_start(self):
        """
            Starting new sequence stops the previous
        """

        self.mark_sequence_end()

        self._sequences.append( VideoAnnotation(self._cur_index) )  

    def mark_sequence_end(self):

        if self._sequences:

            self._sequences[-1].end = self._cur_index

    def save_annotations(self, file_name=None):

        out_file = file_name if file_name is not None else self.output_file

        print("saving annotations to: ", out_file)        

        with open(out_file, 'w') as f:
            for annotation in self._sequences:
                f.write("{},{}\n".format(annotation.start, annotation.end))

    def load_class_names(self, default_values, annotation_class_file):
        """ 
            Load class names from file if given. Class names on separate lines
        """
        if annotation_class_file is None:
            return default_values

        classes = []
        with open(annotation_class_file, 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                classes.append(str(line))

        if len(classes)  == 0:
            return default_values
        else:
            print(f"Read {len(classes)} classes from class file {annotation_class_file}")
            return classes

    def load_saved_annotations(self, annotation_loader, annotation_file):

        """
            For easier customization and different annotation types, the annotation loader 
            is given as an argument.

            If the annotation_file is None, initialize annotations storage for each frame.

            If annotation_file path is given load the detections and make sure the contents 
            of the annotation file are valid for this video.
        """

        frame_annotations = []

        if annotation_file is None:

            for ind in range(self.frame_count):
                # add an empty list of detections for each frame
                frame_annotations.append([])

        else:

            frame_annotations = annotation_loader.load_annotation_file(annotation_file)

            print(f"loaded annotations {frame_annotations}")

        return frame_annotations






    def get_class_color(self, class_name):
        if class_name in self.class_colors:
            return self.class_colors[class_name]
        else:
            return '#ffffff'

    def get_class_colors(self):
        """
            create distinct colors in hsv space
        """
        colors = dict()

        nclasses = len(self.annotation_classes)

        for ind, class_name in enumerate(self.annotation_classes):
            hsv_color = (1.0*ind / nclasses,  .5, .5 )
            rgb_color = tuple([int(255*clr) for clr in colorsys.hsv_to_rgb(*hsv_color)])
            colors[class_name] = '#%02x%02x%02x' % rgb_color

        from pprint import pprint
        print("class colors: ")
        pprint(colors)

        return colors

    def get_class_id(self, class_name):
        if class_name in self.class_ids:
            return self.class_ids[class_name]
        else:
            return -1  

    def get_class_ids(self):
        class_ids = dict()
        for ind, class_name in enumerate(self.annotation_classes):
            class_ids[class_name] = ind 
        return class_ids

    def next_annotation_class(self):
        self._active_annotation_index = (self._active_annotation_index + 1) % len(self.annotation_classes)
        return self.active_annotation


    @property
    def time_between_frames(self):
        if self.fps > 0:
            return 1.0 / self.fps
        else:
            return 0.0

    @property
    def frame_count(self):
        if self.cap is not None:
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        else:
            return 0

    @property
    def current_frame(self):
        return self._cur_index

    @property
    def fps(self):
        if self.cap is not None:
            return int(self.cap.get(cv2.CAP_PROP_FPS))
        else:
            return 0

    @property
    def frame_skip_count(self):
        return self._frame_skip_count

    @frame_skip_count.setter
    def frame_skip_count(self, new_value):
        self._frame_skip_count = new_value

    @property
    def active_annotation(self):
        if len(self.annotation_classes) == 0:
            return ""
        else:            
            return self.annotation_classes[self._active_annotation_index]

    @active_annotation.setter
    def active_annotation(self, new_active):
        try:
            self._active_annotation_index = self.annotation_classes.index(new_active)
        # no such class
        except ValueError:
            pass
    
    
    




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
        return "{}:\n {}".format(self.descript_text, new_text)

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


         # info labels
        self.info_parent = tkinter.Label(self)
        self.info_parent.grid(row=self.root_row_index, column=0)

        # add an active annotation class widget
        self.disp_string = tkinter.StringVar()
        self.disp_string.set(self.vann.active_annotation)
        self.ann_select_widget = tkinter.OptionMenu(self.info_parent, self.disp_string, *self.vann.annotation_classes, command=self.ann_selection_callback)
        self.ann_select_widget.grid(row=0,column=0)

      
        self.info_labels = [UpdateLabel(self.info_parent, 'Frame count', 'frame_count', self.vann),
                            UpdateLabel(self.info_parent, 'Current frame', 'current_frame', self.vann),
                            UpdateLabel(self.info_parent, 'FPS', 'fps', self.vann),
                            UpdateLabel(self.info_parent, 'Frames to skip', 'frame_skip_count', self.vann),
                            UpdateLabel(self.info_parent, 'Time between frames', 'time_between_frames', self.vann)]

        for ind, label in enumerate(self.info_labels):
            label.grid(row=0, column=ind+1)

        
        # Video viewing frame
        self.image_area = tkinter.Canvas(self)
        self.image_area.grid(row=self.root_row_index,column=0)

        # create hidden boxes for all the annotable classes
        self._boxes = [ self.image_area.create_rectangle((0,0,100,100),
                                                     tags='tag'+str(self.vann.get_class_id(class_name)),
                                                     fill="",
                                                     width=2,
                                                     state=tkinter.HIDDEN,

                                                     outline=self.vann.get_class_color(class_name))
                                    for class_name in self.vann.annotation_classes]



        # buttons
        self.button_parent = tkinter.Label(self)
        self.button_parent.grid(row=self.root_row_index, column=0)

        self.buttons = [tkinter.Button(self.button_parent, text="Play", command=self.play_video),
                        tkinter.Button(self.button_parent, text="Pause", command=self.pause_video),
                        tkinter.Button(self.button_parent, text="Next frame", command=self.next_frame),
                        tkinter.Button(self.button_parent, text="Previous frame", command=self.prev_frame),
                        tkinter.Button(self.button_parent, text="Start sequence", command=self.start_ann_seq),
                        tkinter.Button(self.button_parent, text="End sequence", command=self.stop_ann_seq),
                        tkinter.Button(self.button_parent, text="Increase skipped frames", command=self.increase_skip_frames),
                        tkinter.Button(self.button_parent, text="Decrease skipped frames", command=self.decrease_skip_frames),
                        tkinter.Button(self.button_parent, text="Mark annotations", command=self.mark_annotation),
                        tkinter.Button(self.button_parent, text="Save annotations", command=self.save_annotations)]



        # order buttons 
        for ind, but in enumerate(self.buttons):
            but.grid(row=0, column=ind)

        frame = self.vann.get_next_frame()
        self.update_frame(frame)

        # bind events 
        self.bind_events()

        # ready to play the video
        self.play_video_loop()

        # Start the GUI
        self.mainloop() 

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
                self.next_annotation()
        
        # tkinter only allows binding general key pressed, use an inner function to do the work
        self.bind('<Key>', delegate_key_presses)                


    def image_area_clicked(self, event):

        self._original_click_pos = (event.x, event.y)

    def image_area_dragged(self, event):
        """
            redraw the active bbox as dragging
            bboxes are found through their tag (which is their class_name)
        """

        if self._drawing:            
            class_name = self.vann.active_annotation
            # if tag is just a number string, tkinter mixes it with id :/
            tag = 'tag'+str(self.vann.get_class_id(class_name))
            box_id = self.image_area.find_withtag(tag)
            self.image_area.itemconfig(box_id, state=tkinter.NORMAL)
            self.image_area.coords(box_id, *(*self._original_click_pos, event.x, event.y))

            self.image_area.bbox(box_id,(*self._original_click_pos, event.x, event.y) )


    def image_area_released(self, event):

        if self._drawing:
            self._drawing = False


    def update_frame(self, new_frame):

        # Convert the Image object into a TkPhoto object
        image = Image.fromarray(new_frame)
        self.curr_frame = ImageTk.PhotoImage(image=image) 
       
        image_ref = self.image_area.create_image((0,0,), anchor=tkinter.NW, image=self.curr_frame)
        self.image_area.tag_lower(image_ref)

        height, width, clrs = new_frame.shape
        self.image_area.config(width=width, height=height)


    def update_labels(self):
        for label in self.info_labels:
            label.update_text()

        self.disp_string.set(self.vann.active_annotation)

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
            self.obj.update_labels()         

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


    def play_video(self):
        self._video_playing = True

    def pause_video(self):
        self._video_playing = False


    @update_gui
    def mark_annotation(self):
        self._drawing = True
        print("starting annotation marking")   

    @update_gui
    def ann_selection_callback(self, active_name):
        """callback gets the new selected option as argument"""        
        self.vann.active_annotation = active_name 

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
    def start_ann_seq(self):
        self.vann.mark_sequence_start()

    @update_gui
    def stop_ann_seq(self):
        self.vann.mark_sequence_end()

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

