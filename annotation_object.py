
class BoxDetection:

	def __init__(self, point1, point2, class_name, class_id, obj_id):
		"""
			point1 and point2 are the upper left and the lower right corner, respectively.
			tuples of (x,y)
		"""

		self.class_name = class_name
		self.class_id = class_id
		self.obj_id = obj_id

		# store the box coordinates
		self.coords = (point1[0], point1[1], point2[0], point2[1])

	@classmethod
	def from_detection_json(cls, detection_json):

		"""
			given a json formatted detection, create a box object from it
		"""

		p1 = (detection_json['object_coords'][0]['x'], detection_json['object_coords'][0]['y'])
		p2 = (detection_json['object_coords'][1]['x'], detection_json['object_coords'][1]['y'])		

		return cls(p1, p2, detection_json['class_name'], detection_json['class_id'], detection_json['object_id'])

	def __repr__(self):
		return f"{self.__class__.__name__} of class {self.class_name} and object id {self.obj_id} at {self.coords}"

		