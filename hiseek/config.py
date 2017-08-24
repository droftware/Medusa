class Configuration(object):

	def __init__(self, fps, velocity, fixed_time_quanta, num_rays, visibility_angle, verbose):
		self.__fps = fps * 1.0
		self.__velocity = velocity * 1.0
		self.__fixed_time_quanta = fixed_time_quanta
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle
		self.__verbose = verbose

	def get_fps(self):
		return self.__fps

	def get_velocity(self):
		return self.__velocity

	def get_fixed_time_quanta(self):
		return self.__fixed_time_quanta

	def get_num_rays(self):
		return self.__num_rays

	def get_visibility_angle(self):
		return self.__visibility_angle

	def get_verbose(self):
		return self.__verbose

