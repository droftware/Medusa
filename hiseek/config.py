class Configuration(object):

	def __init__(self, fps, velocity, fixed_time_quanta, num_rays, visibility_angle, verbose, save_frame, hider_image, seeker_image, show_fellows, show_opponent, texture_flag, full_screen):
		self.__fps = fps * 1.0
		self.__velocity = velocity * 1.0
		self.__fixed_time_quanta = fixed_time_quanta
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle
		self.__verbose = verbose
		self.__save_frame = save_frame
		self.__hider_image = hider_image
		self.__seeker_image = seeker_image
		self.__show_fellows = show_fellows
		self.__show_opponent = show_opponent
		self.__texture_flag = texture_flag
		self.__full_screen = full_screen

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

	def get_save_frame(self):
		return self.__save_frame

	def get_hider_image(self):
		return self.__hider_image

	def get_seeker_image(self):
		return self.__seeker_image

	def get_show_fellows(self):
		return self.__show_fellows

	def get_show_opponent(self):
		return self.__show_opponent

	def get_texture_flag(self):
		return self.__texture_flag

	def get_full_screen(self):
		return self.__full_screen