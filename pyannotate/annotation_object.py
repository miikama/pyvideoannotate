
import tkinter
import logging


# load logger
logger = logging.getLogger("AnnotationObject")

class BoxDetection:

    def __init__(self, points, class_name, class_id, obj_id, canvas=None, color='#ffffff'):
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
        self.color = "#ffffff"

        # is the annotation visible
        self.visible = True

        # initial drawing of the annotation if a tkinter canvas is given
        if canvas is not None:
            self.draw_annotation(canvas, color)

        logger.debug(f"creating annotation box with tag {self.tag}")

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

    def update_annotation(self, coords=None, visible=True, color=None, class_name=None):
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
                    'object_id' : self.object_id,
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

		