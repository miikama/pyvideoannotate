
import json
import logging

from pyannotate.annotation_object import BoxAnnotation

# load logger
logger = logging.getLogger("AnnotationLoader")

class AnnotationLoader:
	"""
		Basically a BoxAnnotationLoader, since load detected boxes by default
	"""

	def __init__(self, annotation_class=BoxAnnotation):

		self.annotation_class = annotation_class


	def load_annotation_file(self, file_path):

		json_data = None 

		with open(file_path, 'r') as f:			
			json_data = json.load(f)

		# should have annotations for each frame (can be empty)
		if not len(json_data['frames']) == json_data['frame_count']:
			raise RuntimeError('Annotation file invalid, number of annotations and frame count disagree.')

		objects_for_frames = []

		# keep track of all the loaded class names
		class_names = set()
		obj_ids = set()

		# load all the frames
		for frame_ind, frame in enumerate(json_data['frames']):

			# create a list of list of detection for this frame
			objects_for_frames.append( [self.create_detection_object(det) for det in frame['objects']])

			# keep track which class names and object ids are found in the file
			for annotation in objects_for_frames[frame_ind]:
				class_names = class_names.union([annotation.class_name])
				obj_ids = obj_ids.union([annotation.obj_id])


		return objects_for_frames, class_names, obj_ids

			
		
	def create_detection_object(self,detection_json):

		"""
			format the incoming detected json to whatever format wanted
			The default class create is a BoxAnnotation.

			To use different detection formats, override this method
		"""

		print(f"Creating detection object with annotation class {self.annotation_class}")

		return self.annotation_class.from_detection_json(detection_json)


	def save_annotation_file(self, file_path, annotations):

		"""
			Calls the detection objects to json method for each detection.
			Allows different detection classes 
		"""

		root = {
				'frame_count' : len(annotations),
				'frames' : []
				}
		
		
		for frame_ind, frame in enumerate(annotations):

			frame_dict ={
						 'frame_index' : frame_ind,
						 'objects' : [ detection.detection_to_json() for detection in frame ]
						}

			root['frames'].append(frame_dict)

		with open(file_path, 'w') as f:			
			json.dump(root, f, indent=2)




