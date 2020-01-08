
import cv2
import tkinter
import logging


# load logger
logger = logging.getLogger("AnnotationObject")

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class BoxAnnotation:

    def __init__(self, points, class_name, class_id, obj_id, color='#ffffff'):
        """
        point1 and point2 are the upper left and the lower right corner, respectively.
        tuples of (x,y)
        """

        self.class_name = class_name
        self.class_id = class_id
        self.obj_id = obj_id

        # hold a reference to the drawing
        self.draw_ref = None

        # store the box coordinates
        self.coords = points

        self.tag = f"obj_{obj_id}_tag"

        # annotation color
        self.color = color

        # is the annotation visible
        self.visible = True

        logger.debug(f"creating annotation box with tag {self.tag}")

    def draw_annotation_to_array(self, frame, color, active=False):
        """
            Given a numpy array representing an image draw this object.
        """

        
        cv2.rectangle(frame, (self.coords[0],self.coords[1]), (self.coords[2],self.coords[3]), hex_to_rgb(self.color[1:]), thickness=2)
        
        if active:
            spacing = 4
            cv2.rectangle(frame, (self.coords[0] + spacing,self.coords[1] + spacing), (self.coords[2] - spacing,self.coords[3] - spacing), hex_to_rgb(self.color[1:]), thickness=2)



    def draw_annotation(self, canvas,color):
        """
            Given a tkinter canvas object, draw this object.

            For finding the same object but drawn in different frames,
            the object tag is used to find the correct object.
        """

        # update color 
        self.color = color

        # if the draw reference is not None, the annotation has been drawn
        if self.draw_ref is not None:

            state = tkinter.NORMAL if self.visible else tkinter.HIDDEN

            # update color
            canvas.itemconfig(self.draw_ref, outline=color)

            # update visibility
            canvas.itemconfig(self.draw_ref, state=state)

            # update location
            canvas.coords(self.draw_ref, *self.coords)



        # if the annotation has not been draw yet, create a new box
        # First check if the object with this id (and tag) has been drawn already
        else:

             # find boxes that correspond to this object and are already drawn on canvas
            drawn_tags = canvas.find_withtag(self.tag)

            # if the annotation is drawn already, update the current annotation
            if len(drawn_tags) > 0:
                logger.debug(f"Not creating new box for annotation because found one drawn with tags {drawn_tags}")
                self.draw_ref = drawn_tags[0]


            # if the draw ref is still None, this object has not been drawn
            if self.draw_ref is None:
            
                self.draw_ref = canvas.create_rectangle(self.coords,
                                                        tags=self.tag,
                                                        fill="",
                                                        width=2,
                                                        outline=color)

                # move the recently created item to the top
                canvas.tag_raise(self.draw_ref)

    def update_annotation(self, coords=None, visible=True, color=None, class_name=None, class_id=None):
        """
            Update the visibility, position, and/or color of the drawn annotation
        """

        logger.debug(f"Updating annotation with coords: {coords} visible {visible} color {color} and class_name {class_name}")
        # control the visibility
        self.visible = visible

        # update the coordinates is they are given
        self.coords = self.coords if coords is None else coords

        # update the class
        self.class_name = self.class_name if class_name is None else class_name
        self.class_id = self.class_id if class_id is None else class_id

        # update color 
        self.color = self.color if color is None else color 


    def detection_to_json(self):
        """
        example:
            {
              "class_name" : "normal",
              "class_id" : 0,
              "object_id" : 0,
              "object_coords" : [
            	{
            	  "x" : 100,
            	  "y" : 100
            	},
            	{
            	  "x" : 200,
            	  "y" : 200
            	}
              ]
            }

        """

        det_dict = {
                    'class_name' : self.class_name,
                    'class_id' : self.class_id,
                    'object_id' : self.obj_id,
                    'object_coords' : [
                        {
                            'x' : self.coords[0],
                            'y' : self.coords[1]
                        },
                        {
                            'x' : self.coords[2],
                            'y' : self.coords[3]
                        }
                    ]
        }



        return det_dict


    @classmethod
    def from_detection_json(cls, detection_json):

        """
        given a json formatted detection, create a box object from it
        """

        points = (detection_json['object_coords'][0]['x'], detection_json['object_coords'][0]['y'], 
                detection_json['object_coords'][1]['x'], detection_json['object_coords'][1]['y'])		

        return cls(points, detection_json['class_name'], detection_json['class_id'], detection_json['object_id'])


    def __repr__(self):
        return f"{self.__class__.__name__} of class {self.class_name} and object id {self.obj_id} at {self.coords}"

		


class TextBoxAnnotation(BoxAnnotation):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.text = ""

    def update_annotation(self, text=None, **kwargs):

        super().update_annotation(**kwargs)

        self.text = self.text if text is None else text

    @classmethod
    def from_detection_json(cls, detection_json):
        """
            Do the same as parent class but just add the extra text
        """
        
        # this calls the parent method but returns TextBoxAnnotation :)
        basic_annotation = super(TextBoxAnnotation, cls).from_detection_json(detection_json)

        if 'text' not in detection_json:
            print(f"No text found for anntoation {basic_annotation}, cannot add it")
            return basic_annotation

        basic_annotation.update_annotation(text=detection_json['text'])

        print(f"Loaded annotation {basic_annotation}")

        return basic_annotation

    def detection_to_json(self):
        """
            The same as parent but with added text
        """
        parent_json = super().detection_to_json()

        parent_json['text'] = self.text

        return parent_json

    def __repr__(self):
        return f"{self.__class__.__name__} of class {self.class_name} and object id {self.obj_id} at {self.coords} with text {self.text}"





