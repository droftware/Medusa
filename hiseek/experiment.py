import simulator
import statistic

class Experiment(object):
	"""
		Responsible for executing the simulations in the manner demanded by the user and 
		tracking the statistics involved
	"""

	def __init__(self, display, num_runs, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, verbose):
		self.__display = display
		self.__num_runs = num_runs
		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file
		self.__verbose = verbose

	def run(self):
		sim = simulator.Simulator(self.__display, self.__mode_hiders, self.__mode_seekers, self.__num_hiders, self.__num_seekers, self.__map_id, self.__input_file, self.__output_file, self.__verbose)
		sim.simulate()
			
