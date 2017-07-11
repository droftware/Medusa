import numpy as np

import grid
import coord

class BasicMapManager(object):
	'''
		Each agent is asoociated with a map manager which helps it to manage
		its map related data.
	'''
	def __init__(self, mapworld):
		self.__map = mapworld
		num_rows = self.__map.get_num_rows()
		num_cols = self.__map.get_num_cols()
		self.__heat_field = Grid(num_rows, num_cols)

		# Prepare heat map
		for i in range(num_rows):
			for j in range(num_cols):
				if self.__map.is_obstacle(i, j):
					for a in range(1, 3):
						for x in [-a, a]:
							for y in [-a, a]:
								row_pos = i + x
								col_pos = j + y
								if self.__map.is_inside(row_pos, col_pos):
									if self.__map.is_free(row_pos, col_pos):
										value = self.__heat_field.get(row_pos, col_pos) 
										self.__heat_field.set(row_pos, col_pos, value + 1)

	def get_heat_value(self, coordinate):
		x, y = coordinate.get_tuple()
		assert(self.__map.is_inside(x, y))
		return self.__heat_field.get(x, y)

	def is_inside(self, coordinate):
		x, y = coordinate.get_tuple()
		return self.__map.is_inside(x, y)

	def is_obstacle(self, coordinate):
		x, y = coordinate.get_tuple()
		return self.__map.is_obstacle(x, y)



