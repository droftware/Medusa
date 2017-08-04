import os.path

import numpy as np

import hscodes

class Grid(object):
	"""
		Provides the grid data type to be used during hide and seek simulations
	"""

	def __init__(self, num_rows, num_cols):
		self._grid = np.zeros((num_rows, num_cols), np.int32)
		self._num_rows = num_rows
		self._num_cols = num_cols

	def is_inside(self, x, y):
		return x >= 0 and y >= 0 and x < self._num_rows and y < self._num_cols

	def get(self, x, y):
		return self._grid[x, y]

	def set(self, x, y, value):
		self._grid[x, y] = value

	def get_num_rows(self):
		return self._num_rows

	def get_num_cols(self):
		return self._num_cols


	# def set(self, x, y, value):
	# 	self._grid[x, y] = value 

	def __str__(self):
		grid_string = '* '

		for i in range(self._num_cols):
			grid_string += str(i) + '| '
		grid_string += '\n'

		for i in range(self._num_rows):
			grid_string += str(i) + '|'
			for j in range(self._num_cols):
				grid_string += str(self._grid[i, j]) + ', '
			grid_string += '\n'
		return grid_string


class Map(Grid):
	"""
		Map used during the simulation of hide and seek
	"""

	map_list = []
	def __init__(self, map_id):
		map_name = 'id_' + str(map_id) + '.grid'
		# print('Path:', map_name)
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
		Map.map_list.append(self)

		# super(Map, self).__str__()

	def is_free(self, x, y):
		assert(self.is_inside(x, y))
		return self._grid[x, y] == hscodes.FREE

	def is_obstacle(self, x, y):
		assert(self.is_inside(x, y))
		return self._grid[x, y] == hscodes.OBSTACLE

	def is_hider(self, x, y):
		assert(self.is_inside(x, y))
		return self._grid[x, y] == hscodes.HIDER

	def is_seeker(self, x, y):
		assert(self.is_inside(x, y))
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

	def clear(self):
		'''
			Sets all the non-obstacle cells to free i.e. clears the presence
			of any hiders, seekers and their visibility
		'''
		for i in range(self._num_rows):
			for j in range(self._num_cols):
				if not self.is_obstacle(i, j):
					self._grid[i, j] = hscodes.FREE

	def __get_visibility(self, i, j, multiplier, orientation):
		assert(self.is_free(i, j))
		assert(multiplier == -1 or multiplier == 1)
		assert(orientation == -1 or orientation == 1)
		visible_cells = []
		blocked = []
		lower_stop = None
		upper_stop = None
		x_limit = None

		if orientation == 1:
			x_limit = self._num_rows
		elif orientation == -1:
			x_limit = self._num_cols

		print('x_limit:', x_limit)

		for x in range(x_limit):
			if lower_stop == None:
				lower_limit = -1*x
			else:
				lower_limit = lower_stop
			if upper_stop == None:
				upper_limit = x
			else:
				upper_limit = upper_stop 
			for y in range(lower_limit, upper_limit+1):
				if orientation == 1:
					a = i + (multiplier * x)
					b = j + y
				elif orientation == -1:
					a = i + y
					b = j + (multiplier * x)

				if not self.is_inside(a, b):
					continue

				print(i-x,':',j+y)
				if self._grid[a, b] == hscodes.OBSTACLE:
					print('grid cell', a,',',b, 'is an obstacle')

					if y == -1*x:
						lower_stop = y + 1
					elif y == x:
						upper_stop = y - 1
					else:
						if orientation == 1:
							blocked.append(b)
						elif orientation == -1:
							blocked.append(a)
					continue
				if orientation == 1:
					if b in blocked:
						continue
				elif orientation == -1:
					if a in blocked:
						continue

				self._grid[a, b] = 9
				visible_cells.append((a, b))
		return visible_cells

	def get_visibility_north(self, i, j):
		return self.__get_visibility(i, j, -1, 1)

	def get_visibility_south(self, i, j):
		return self.__get_visibility(i, j, 1, 1)

	def get_visibility_east(self, i, j):
		# right
		return self.__get_visibility(i, j, 1, -1)

	def get_visibility_west(self, i, j):
		# left
		return self.__get_visibility(i, j, -1, -1)
