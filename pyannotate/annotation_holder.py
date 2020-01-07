from typing import List, Dict
import os
import colorsys
import cv2
import logging 

from annotation_loader import AnnotationLoader
from annotation_object import BoxDetection

# load logger
logger = logging.getLogger("VideoAnnotations")


class Annotation:

    _frames = []

    _cur_index = 0

    # list of tuples (start_index, end_index) that mark the video sequence 
    _sequences = []


    _defaults = {
        'annotation_frame_rate': 5,
        'output_file': 'annotations.json',
        'annotation_classes': ["class1", "class2"]
    }

    def __init__(self, output_file, annotation_class_file=None, annotation_file=None):

        # set up default values
        self.__dict__.update(self._defaults) 

        self.output_file = output_file if output_file is not None else self.output_file

        # load class names from file or use defaults if no file given
        self.annotation_classes = self.load_class_names(self.annotation_classes, annotation_class_file)      

        self.annotation_object_ids = set()  

        # init an annotation loader 
        self.annotation_loader = AnnotationLoader()

        # add the annotation file class names to the pool of possible classes
        self.frame_annotations = self.load_saved_annotations(annotation_file)

        # dictionary of class name -> color
        self.class_colors = self.get_class_colors()

        # dictionary of class name -> class_id 
        self.class_ids =  self.get_class_ids()

        # which annotation we are going at
        self._active_annotation_class_index = -1

        # index of the object we are currently annotating
        self._active_annotation_object_index = -1

    def get_next_frame(self):

        self._cur_index = min(self._cur_index + 1, self.frame_count-1)

        return self.read_new_frame()

    def read_new_frame(self):
        """
            reads an image in at _cur_index 

            @return: rgb image as numpy array
        """
        raise NotImplementedError("One should implement this in the childred class") 
        
    def init_new_frame(self):
        """
            A method to be called after changing frames
        """
        # update the annotation objects for this frame
        if len(self.frame_annotations[self._cur_index]) > 0:
            self._active_annotation_object_index = 0        
        else:
            self._active_annotation_object_index = -1


    def get_prev_frame(self):

        self._cur_index = max(self._cur_index -1, 0)

        return self.read_new_frame()

    def save_annotations(self, file_name=None):

        out_file = file_name if file_name is not None else self.output_file

        print(f"saving annotations to: ", out_file)        

        self.annotation_loader.save_annotation_file(out_file, self.frame_annotations)

    def load_class_names(self, default_values, annotation_class_file: str) -> List[str]:
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

    def load_saved_annotations(self, annotation_file):

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

            frame_annotations, new_class_names, new_ids = self.annotation_loader.load_annotation_file(annotation_file)

            # combine the new and old classes
            self.annotation_classes = list(set(self.annotation_classes).union(new_class_names))

            # combine the new and old obj ids
            self.annotation_object_ids = self.annotation_object_ids.union(new_ids)

            if not len(frame_annotations) == self.frame_count:
                raise RuntimeError("Wrong amount of annotations in the annotation file.")

            total_objects = sum([len(detects) for detects in frame_annotations]) 

            print(f"loaded {len(frame_annotations)} annotations")
            print(f"And {total_objects} objects")

        return frame_annotations

    def add_annotation(self, points=None):
        """Add new annotation for current frame"""    

        if len(self.active_annotation_class) == 0:
            self.next_annotation_class()

        class_name = self.active_annotation_class

        # if the there is no current annotation object create new
        new_obj_id = self.create_annotation_object()

        print(f"new obj_id is {new_obj_id}")

        new_points = (0,0,0,0)
        if points is not None:
            new_points = points

        annotation = BoxDetection(new_points,
                                  class_name,
                                  self.class_ids[class_name],
                                  new_obj_id,                                  
                                  color=self.class_colors[class_name])

        self.frame_annotations[self._cur_index].append(annotation)  

        self.active_annotation_object = new_obj_id   

        print(f"added annotation with class {class_name}")

    def update_annotation(self, points):

        if self.active_annotation_object:            
            # the detection object currently active            
            self.active_annotation_object.update_annotation(coords=points)
        else:
            print(f"trying to annotate nonexisting object")

    def create_annotation_object(self):
        """Adds a new object id """
        obj_ids = self.annotation_object_ids

        new_id = 0
        # handle empty object ids
        if len(obj_ids) > 0:
            largest_obj_id = max(obj_ids) 
            new_id = largest_obj_id + 1

        self.annotation_object_ids.add(new_id)

        return new_id


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

        #from pprint import pprint
        #print("class colors: ")
        #pprint(colors)

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

    def get_annotations_for_current_frame(self):
        if len(self.frame_annotations) == 0 or self._cur_index < 0:
            return []

        return self.frame_annotations[self._cur_index]        
            
    def next_annotation_class(self):
        if len(self.annotation_classes) == 0:
            return None

        # if the first to annotate, -1 becomes 0
        self._active_annotation_class_index = (self._active_annotation_class_index + 1) % len(self.annotation_classes)
        self.active_annotation_class = self.annotation_classes[self._active_annotation_class_index]
        return self.active_annotation_class

    def next_annotation_object_in_current_frame(self):
        current_frame_annotations = self.get_annotations_for_current_frame()        

        if not current_frame_annotations:
            self._active_annotation_object_index = -1
            return None

        self._active_annotation_object_index = (self._active_annotation_object_index + 1) % len(current_frame_annotations)

        self.active_annotation_class = self.active_annotation_object.class_name
        return self.active_annotation_object

    def delete_active_annotation_object(self):
        active_object = self.active_annotation_object
        if active_object is None:
            return

        self.frame_annotations[self._cur_index].pop(self._active_annotation_object_index)

        # after taking the active out of the list, the active annotation object index should be updated
        self.next_annotation_object_in_current_frame()
 

    def get_frame_annotations(self, frame_ind=None):
        """Return the detection objects for current frame"""        

        if frame_ind is None:            
            return self.frame_annotations[self._cur_index] 
        else:
            return self.frame_annotations[frame_ind] 

    @property
    def frame_count(self):
        raise NotImplementedError("Implement this in child class")
        
    @property
    def current_frame(self):
        return self._cur_index

    @property
    def active_annotation_class(self):
        if self._active_annotation_class_index < 0:
            return ""

        if len(self.annotation_classes) == 0:
            return ""
        
        return self.annotation_classes[self._active_annotation_class_index]

    @active_annotation_class.setter
    def active_annotation_class(self, new_active: str):
        """ 
            Changes the class of the active annotation object
        """
        try:
            # get the index of the class to annotation
            
            self._active_annotation_class_index = self.annotation_classes.index(new_active)

            print(f"Changing active annotation class to {new_active} which has index {self._active_annotation_class_index}")

            # change the annotation class of the object
            active_object = self.active_annotation_object
            if active_object is not None:
                active_object.update_annotation(class_name=self.active_annotation_class,
                                                class_id=self._active_annotation_class_index,
                                                color=self.class_colors[self.active_annotation_class])

        # no such class
        except ValueError:
            raise ValueError("Should not happen")
            #pass

    @property
    def active_annotation_object_id(self):
        active_obj = self.active_annotation_object
        if active_obj:
            return active_obj.obj_id
        else:
            return -1        

    @property
    def active_annotation_object(self):      
        if self._active_annotation_object_index >= 0:
            return self.frame_annotations[self._cur_index][self._active_annotation_object_index]
        else:
            return None

    @active_annotation_object.setter
    def active_annotation_object(self, object_id):
        """ 
            Find the index of the annotation with the object 
            id from the current frames annotations 
        """
        found = False        
        for ind, annotation in enumerate(self.frame_annotations[self._cur_index]):
            if annotation.obj_id == object_id:
                self._active_annotation_object_index = ind                
                found = True
        self._active_annotation_object_index = -1 if not found else self._active_annotation_object_index

        self.active_annotation_class = self.active_annotation_object.class_name
        
    
    @property
    def current_frame_object_ids(self):
        """return the object ids of objects in current frame"""
        obj_ids = [annotation.obj_id for annotation in self.get_frame_annotations()]
        if len(obj_ids) > 0:
            return obj_ids 
        else:
            return [-1]

class VideoAnnotations(Annotation):
    

    def __init__(self, annotation_vid, output_file, annotation_class_file=None, annotation_file=None):

        # open video capture, the size of the video is used to deduce the frame count. This needs 
        # to happen before initializing the parent class
        self.cap = self.open_video(annotation_vid)

        # call the parent constructor
        super().__init__(output_file, annotation_class_file, annotation_file)


        # number of frames to skip in the next/previous frame call
        self._frame_skip_count = 0

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

        _, frame = self.cap.read()        

        #Rearrange the color channel
        frame = frame[:,:,::-1]

        self.init_new_frame()
        
        return frame

    def get_prev_frame(self):

        self._cur_index = max(self._cur_index -1 - self.frame_skip_count, 0)

        return self.read_new_frame()    

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

    


class ImageAnnotations(Annotation):
    """
        Goes through an image folder 
    """

    # TODO: add more image types that are supported by opencv
    supported_file_types = ('png', 'jpg', 'jpeg')

    def __init__(self, input_directory, output_file, annotation_class_file=None, annotation_file=None):

        # image files in folder
        self._image_files = self.read_image_names(input_directory)

        print(f"Found image files: {self._image_files}")

        # call the parent constructor
        super().__init__(output_file, annotation_class_file, annotation_file)

    def read_image_names(self, folder):

        print(f"looking at image in folder {folder}")

        if not os.path.exists(folder):
            return None

        image_file_paths = []

        for fname in os.listdir(folder):

            file_name, file_ext = os.path.splitext(fname)

            # take extension without dot, .png -> png
            if file_ext[1:] in ImageAnnotations.supported_file_types:
                image_file_paths.append(os.path.join(folder, fname))

        return image_file_paths


    def read_new_frame(self):
        
        cur_image_path = self._image_files[self._cur_index]

        if not os.path.exists(cur_image_path):
            raise OSError(f"No image file found at path: {cur_image_path} for image index {self._cur_index}")

        frame = cv2.cvtColor(cv2.imread(cur_image_path), cv2.COLOR_BGR2RGB)

        self.init_new_frame()

        return frame
    
    @property
    def frame_count(self):
        return len(self._image_files)

 
    

