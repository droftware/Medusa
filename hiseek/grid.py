import os.path

import numpy as np

import hscodes

class Grid(object):
	"""
		Provides the grid data type to be used during hide and seek simulations
	"""

	def __init__(self, num_rows, num_cols):
		self._grid = np.zeros((num_rows, num_cols), np.int32)
		self.__num_rows = num_rows
		self.__num_cols = num_cols

	def is_inside(self, x, y):
		return x >= 0 and y >= 0 and x < self.__num_rows and y < self.__num_cols

	def get(self, x, y):
		return self._grid[x, y]

	def set(self, x, y, value):
		self._grid[x, y] = value 

	def __str__(self):
		for i in range(self.__num_rows):
			for j in range(self.__num_cols):
				print(str(self._grid[i, j]) + ', '),
			print()


class Map(Grid):
	"""
		Map used during the simulation of hide and seek
	"""
	def __init__(self, map_id):
		map_name = 'id_' + str(map_id) + '.grid'
		print('Path:', map_name)
		assert(os.path.isfile(map_name))
		f = open(map_name, 'r')
		map_list = f.readlines()
		num_rows = -1
		num_cols = -1

		# Find out num_rows and num_cols 
		for line in map_list: 
			line.strip()
			if len(line) != 0:
				if num_rows == -1 and num_cols == -1:
					num_rows = 0
					num_cols = len(line.split(','))
				num_rows += 1
				assert(len(line.split(',')) == num_cols)

		super(Map, self).__init__(num_rows, num_cols)

		# Fill the grid with map info
		row = 0
		for line in map_list:
			line.strip()
			if len(line) != 0:
				line = line.split(',')
				for j in range(num_cols):
					numcode = int(line[j])
					assert(numcode == hscodes.FREE or numcode == hscodes.OBSTACLE)
					if numcode == 0:
						self._grid[row, j] = hscodes.FREE
					elif numcode == 1:
						self._grid[row, j] = hscodes.OBSTACLE
			row += 1

		# super(Map, self).__str__()

	def is_free(self, x, y):
		assert(is_inside(self, x, y))
		return self._grid[x, y] == hscodes.FREE

	def is_hider(self, x, y):
		assert(is_inside(self, x, y))
		return self._grid[x, y] == hscodes.HIDER

	def is_seeker(self, x, y):
		assert(is_inside(self, x, y))
		return self._grid[x, y] == hscodes.SEEKER

	def set_hider(self, x, y):
		self._grid[x, y] = hscodes.HIDER

	def set_seeker(self, x, y):
		self._grid[x, y] = hscodes.SEEKER

	def set_visibility_hider(self, x, y):
		self._grid[x, y] = hscodes.VISIBILITY_HIDER

	def set_visibility_seeker(self, x, y):
		self._grid[x, y] = hscodes.VISIBILITY_SEEKER

	def set_free(self, x, y):
		self._grid[x, y] = hscodes.FREE





