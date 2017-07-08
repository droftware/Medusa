import statistic
import grid

class Simulator(object):
	"""
		Responsible for one complete simulation
	"""

	def __init__(self, display, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, verbose):
		self.__display = display
		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file
		self.__verbose = verbose
		self.__stats = statistic.Statistic(num_hiders, num_seekers)

		self.__map = grid.Map(map_id)


