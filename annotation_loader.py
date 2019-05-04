
import json

from annotation_object import BoxDetection


class AnnotationLoader:
	"""
		Basically a BoxAnnotationLoader, since load detected boxes by default
	"""


	def load_annotation_file(self, file_path):

		json_data = None 

		with open(file_path, 'r') as f:			
			json_data = json.load(f)

		# should have annotations for each frame (can be empty)
		if not len(json_data['frames']) == json_data['frame_count']:
			raise RuntimeError('Annotation file invalid, number of annotations and frame count disagree.')

		objects_for_frames = []

		# load all the frames
		for frame_ind, frame in enumerate(json_data['frames']):

			# create a list of list of detection for this frame
			objects_for_frames.append( [self.create_detection_object(det) for det in frame['objects']])

		return objects_for_frames

			
		
	def create_detection_object(self,detection_json):

		"""
			format the incoming detected json to whatever format wanted
			The default class create is a BoxDetection.

			To use different detection formats, override this method
		"""

		return BoxDetection.from_detection_json(detection_json)


