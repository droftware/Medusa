
class Statistic(object):
	"""
		Stores various kind of in-game statistics for one complete simulation.
	"""

	def __init__(self, num_hiders, num_seekers):
		self.__total_time = 0
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__catch_time = [0 for i in range(self.__num_hiders)]
		self.__hider_paths = [[] for i in range(self.__num_hiders)]
		self.__seeker_paths = [[] for i in range(self.__num_seekers)]
		self.__avg_seeker_visibility = 0
		self.__avg_hider_visibility = 0

	def update_seeker_path(self, seeker_num, position):
		self.__seeker_paths[seeker_num].append((position.get_x(), position.get_y()))

	def update_hider_path(self, hider_num, position):
		self.__hider_paths[hider_num].append((position.get_x(), position.get_y()))

	def update_hider_caught_time(self, hider_num, caught_time):
		self.__catch_time[hider_num] = caught_time

	def print_statistic(self):
		print('Seeker Paths:')
		for i in range(self.__num_seekers):
			print('Seeker:', i, self.__seeker_paths[i])

		print()
		print('Hider Paths')
		for i in range(self.__num_hiders):
			print('Hider:', i, self.__hider_paths[i])

		print()
		print('Hider caught times')
		for i in range(self.__num_hiders):
			print('Hider:', i, 'caught at time step:', self.__catch_time[i])

