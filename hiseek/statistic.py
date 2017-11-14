
class Statistic(object):
	"""
		Stores various kind of in-game statistics for one complete simulation.
	"""

	def __init__(self, num_hiders, num_seekers, map_id, sim_turn):
		self.__total_time = 0
		self.__map_id = map_id
 		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__catch_time = [0 for i in range(self.__num_hiders)]
		self.__hider_paths = [[] for i in range(self.__num_hiders)]
		self.__seeker_paths = [[] for i in range(self.__num_seekers)]
		self.__avg_seeker_visibility = 0
		self.__avg_hider_visibility = 0
		self.__sim_turn = sim_turn

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

	def write_statistic(self):
		output_file = 'hs_' + str(self.__sim_turn) + '_.statistic'
		f = open(output_file, 'w')
		f.write('map_id:' + str(self.__map_id) + '\n')
		f.write('num_hiders:' + str(self.__num_hiders) + '\n')
		f.write('num_seekers:' + str(self.__num_seekers) + '\n')

		f.write('hider_paths:' + '\n')
		for i in range(self.__num_hiders):
			path_token = ''
			first = True
			for position in self.__hider_paths[i]:
				if not first:
					path_token += '; '
				else:
					first = False
				path_token += str(position[0]) + ',' + str(position[1])
			f.write(path_token + '\n')

		f.write('seeker_paths:' + '\n')
		for i in range(self.__num_seekers):
			path_token = ''
			first = True
			for position in self.__seeker_paths[i]:
				if not first:
					path_token += '; '
				else:
					first = False
				path_token += str(position[0]) + ',' + str(position[1])
			f.write(path_token + '\n')

		f.write('caught_times:' + '\n')
		for i in range(self.__num_hiders):
			f.write(str(self.__catch_time[i]) + '\n')

		f.close()








