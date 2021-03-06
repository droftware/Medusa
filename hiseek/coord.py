import math

class Coord(object):

	# All valid actions
	north = -1, 0
	south = 1, 0
	east = 0, 1
	west = 0, -1
	north_east = -1, 1
	north_west = -1, -1
	south_east = 1, 1
	south_west = 1, -1
	stop = 0, 0

	# all_actions = [north, south, east, west, north_east, north_west, south_east, south_west]
	# all_actions_string = ['north', 'south', 'east', 'west', 'north_east', 'north_west', 'south_east', 'south_west']
	all_actions_mapping = {}
	all_actions_mapping['north'] = north
	all_actions_mapping['south'] = south
	all_actions_mapping['east'] = east
	all_actions_mapping['west'] = west
	all_actions_mapping['north_east'] = north_east
	all_actions_mapping['north_west'] = north_west
	all_actions_mapping['south_east'] = south_east
	all_actions_mapping['south_west'] = south_west

	def __init__(self, x, y):
		self.__x = x
		self.__y = y
		self.__prev_x = None
		self.__prev_y = None

	def __str__(self):
		coord_string = '(' + str(self.__x) + ', ' + str(self.__y) + ')'
		return coord_string

	def __eq__(self, other):
		if isinstance(other, Coord):
			if self.__x == other.__x and self.__y == other.__y:
				return True
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)


	def get_x(self):
		return self.__x

	def get_y(self):
		return self.__y

	def get_tuple(self):
		return self.__x, self.__y

	def get_all_actions(self):
		return Coord.all_actions_mapping.keys()

	def __set_prev(self):
		self.__prev_x = self.__x
		self.__prev_y = self.__y

	def revert_action(self):
		self.__x = self.__prev_x
		self.__y = self.__prev_y

	def get_euclidean_distance(self, other):
		diff_x = self.get_x() - other.get_x()
		diff_y = self.get_y() - other.get_y()
		return math.sqrt(diff_x*diff_x + diff_y*diff_y)

	@staticmethod
	def to_radians(degrees):
		return math.pi * degrees / 180.0

	def move_action(self, action):
		assert(action in Coord.all_actions_mapping)
		move = Coord.all_actions_mapping[action]
		self.__move_action_raw(move)

	def __move_action_raw(self, raw_action):
		self.__set_prev()
		self.__x += raw_action[0]
		self.__y += raw_action[1]

	def move_north(self):
		self.__move_action_raw(Coord.north)

	def move_south(self):
		self.__move_action_raw(Coord.south)

	def move_east(self):
		self.__move_action_raw(Coord.east)

	def move_west(self):
		self.__move_action_raw(Coord.west)

	def move_north_east(self):
		self.__move_action_raw(Coord.north_east)

	def move_north_west(self):
		self.__move_action_raw(Coord.north_west)

	def move_south_east(self):
		self.__move_action_raw(Coord.south_east)

	def move_south_west(self):
		self.__move_action_raw(Coord.south_west)
