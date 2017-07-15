import statistic
import grid
import team
import percept

class Simulator(object):
	"""
		Responsible for one complete simulation
	"""

	mode_type_hiders = ['random']
	mode_type_seekers = ['random']

	def __init__(self, display, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, verbose, max_steps=1000):
		self.__display = display
		assert(mode_hiders in Simulator.mode_type_hiders)
		assert(mode_seekers in Simulator.mode_type_seekers)
		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file
		self.__verbose = verbose
		self.__stats = statistic.Statistic(num_hiders, num_seekers)
		self.__max_steps = max_steps

		self.__map = grid.Map(map_id)

	def simulate(self):
		hider_map = copy.deepcopy(self.__map)
		seeker_map = copy.deepcopy(self.__map)

		hiders_caught = 0

		if self.__mode_hiders == 'random':
			hider_team = team.RandomHiderTeam(self.__num_hiders, hider_map)
		
		if self.__mode_seekers == 'random':
			seeker_team = team.RandomSeekerTeam(self.__num_seekers, seeker_map)

		while hiders_caught < self.__num_hiders and time_step < self.__max_steps:
			# update the percept of each robot





