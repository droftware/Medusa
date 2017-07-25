import math
import os

import numpy as np

import gamemap
import coord
import action

class BasicMapManager(object):
	'''
		Each agent is asoociated with a map manager which helps it to manage
		its map related data.
	'''
	def __init__(self, mapworld, fps, velocity, offset = 20, inference_map=True):
		self.__mapworld = mapworld
		self.__offset = offset
		self.__num_rows = math.ceil((mapworld.get_map_width() * 1.0)/offset)
		self.__num_cols = math.ceil((mapworld.get_map_height() * 1.0)/offset)
		self.__fps = fps
		self.__dt = 1.0/fps
		self.__velocity = velocity
		self.__visibility = None
		self.__obstruction = None
		self.__obstruction_quarts = (0, 0, 0, 0)
		self.__visibility_quarts = (0, 0, 0, 0)

		if inference_map:
			map_name = mapworld.get_map_name()
			vis_file = map_name.split('.')[0] + '.visibility'
			obs_file = map_name.split('.')[0] + '.obstruction'
			if os.path.isfile(vis_file) and os.path.isfile(obs_file):
				print('Loading files')
				self.__visibility = np.loadtxt(vis_file)
				self.__obstruction = np.loadtxt(obs_file)
			else:
				print('Creating inferences XX')
				self.__visibility = np.zeros((self.__num_rows, self.__num_cols))
				self.__obstruction = np.zeros((self.__num_rows, self.__num_cols))
				print('Entered map manager')
				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						position = coord.Coord(i * self.__offset, j * self.__offset)
						if self.__mapworld.check_obstacle_collision(position):
							self.__visibility[i, j] = -1
							self.__obstruction[i, j] = -1

				print('Filled all obstacles')
				print(self.__visibility)

				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						print('Analyzing:',i,j)
						coord_vis = coord.Coord(i * self.__offset, j * self.__offset)
						if self.__visibility[i, j] != -1:
							visibility_polygon = self.__mapworld.get_visibility_polygon(coord_vis, 0, 100, 180)
							for a in range(self.__num_rows):
								for b in range(self.__num_cols):
									if self.__obstruction[a, b] != -1:
										coord_obs = coord.Coord(a * self.__offset, b * self.__offset)
										if visibility_polygon.is_point_inside(coord_obs):
											self.__visibility[i, j] += 1
											self.__obstruction[a, b] += 1

				np.savetxt('visibility.txt',self.__visibility)
				np.savetxt('obstruction.txt', self.__obstruction)

				self.__obstruction_quarts[4] = np.amax(self.__obstruction)
				self.__obstruction_quarts[0] = np.amin(self.__obstruction)
				self.__obstruction_quarts[2] = np.mean(self.__obstruction)
				self.__obstruction_quarts[1] = (self.__obstruction_quarts[0] + self.__obstruction_quarts[2])/2.
				self.__obstruction_quarts[3] = (self.__obstruction_quarts[2] + self.__obstruction_quarts[4])/2.

				self.__max_obstruction = 


	def get_map(self):
		return self.__mapworld

	def __get_position_index(self, position):
		row = int(position.get_x())%self.__offset
		col = int(position.get_y())%self.__offset
		return row, col

	def get_visibility_value(self, position):
		row, col = self.__get_position_index(position)
		return self.__visibility[row, col]

	def get_obstruction_value(self, position):
		row, col = self.__get_position_index(position)
		return self.__obstruction[row, col]

	def get_blocked_value(self, position):
		return self.__mapworld.check_obstacle_collision(position)

	def get_action_map(self, position):
		results = {}
		for move in action.Action:
			if move != action.Action.Stop:
				rotation = action.ROTATION[move]
				rotation_x = math.cos(coord.Coord.to_radians(-rotation))
				rotation_y = math.sin(coord.Coord.to_radians(-rotation))
				vx = self.__velocity * rotation_x
				vy = self.__velocity * rotation_y
				x = position.get_x() + vx * self.__dt
				y = position.get_y() + vy * self.__dt
				results[move] = coord.Coord(x, y)
		return results

