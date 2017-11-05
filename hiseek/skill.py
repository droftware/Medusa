from abc import ABCMeta, abstractmethod
import random

import coord

import numpy as np

class Skill(object):

	__metaclass__ = ABCMeta

	def __init__(self, agent_type, team, map_manager):
		self._agent_type = agent_type
		self._team = team
		self._map_manager = map_manager

class RandomOpeningSkill(Skill):

	def __init__(self, agent_type, team, map_manager):
		super(RandomOpeningSkill, self).__init__(agent_type, team, map_manager)
		self.__opening_positions = {}
		self.__openings_created = False		

	def get_opening_position(self, rank, idx):
		assert(rank < self._team.get_ranks())
		assert(idx < self._team.get_num_rankers(rank))
		if not self.__openings_created:
			self.__set_opening()
			self.__openings_created = True
		return self.__opening_positions[(rank, idx)]

	def __check_within_obstacle(self, position):
		gamemap = self._map_manager.get_map()
		num_polygons = gamemap.get_num_polygons()
		for i in range(num_polygons):
			polygon = gamemap.get_polygon(i)
			if polygon.is_point_inside(position):
				return True
		return False

	def __check_already_occupied(self, position):
		for value in self.__opening_positions.values():
			if position == value:
				return True
		return False

	def __set_opening(self):
		gamemap = self._map_manager.get_map()
		max_rank = self._team.get_ranks()
		for i in reversed(range(max_rank)):
			for j in range(self._team.get_num_rankers(i)):
				found_position = False
				while not found_position:
					position = coord.Coord(random.randint(0, gamemap.get_map_width()), random.randint(0, gamemap.get_map_height()))
					if not self.__check_within_obstacle(position) and not self.__check_already_occupied(position):
						self.__opening_positions[(i, j)] = position
						found_position = True

class LineOpeningSkill(Skill):

	def __init__(self, agent_type, team, map_manager):
		super(LineOpeningSkill, self).__init__(agent_type, team, map_manager)
		self.__opening_positions = {}
		self.__openings_created = False	
		self.__x_offset = 5
		self.__y_offset = 0
		self.__ground_coord = coord.Coord(100, 5)	

	def get_opening_position(self, rank, idx):
		assert(rank < self._team.get_ranks())
		assert(idx < self._team.get_num_rankers(rank))
		if not self.__openings_created:
			self.__set_opening()
			self.__openings_created = True
		return self.__opening_positions[(rank, idx)]

	def __set_opening(self):
		max_rank = self._team.get_ranks()
		position = self.__ground_coord
		for i in reversed(range(max_rank)):
			for j in range(self._team.get_num_rankers(i)):
				self.__opening_positions[(i, j)] = position
				position = coord.Coord(position.get_x() + self.__x_offset, position.get_y() + self.__y_offset)



class UCBOpeningSkill(Skill):
	def __init__(self, agent_type, team, map_manager, macro_UCB, randomOpening=False):
		super(UCBOpeningSkill, self).__init__(agent_type, team, map_manager)
		self.__macro_UCB = macro_UCB
		self.__opening_positions = {}
		self.__openings_created = False
		self.__randomOpening = randomOpening


	def get_opening_position(self, rank, idx):
		assert(rank < self._team.get_ranks())
		assert(idx < self._team.get_num_rankers(rank))
		if not self.__openings_created:
			self.__set_opening()
			self.__openings_created = True
		return self.__opening_positions[(rank, idx)]

	def __set_opening(self):
		max_rank = self._team.get_ranks()
		opening_points = []
		num_agents = self._team.get_num_agents()
		num_strategic_points = self._map_manager.get_num_strategic_points()
		if num_agents <= num_strategic_points:
			if self.__randomOpening:
				opening_points = np.random.choice(num_strategic_points, num_agents, replace=False)
			else:
				opening_points = self.__macro_UCB.get_greatest_actions(num_agents)
		else:
			opening_points = np.random.choice(num_strategic_points, num_agents)
		st_idx = 0
		for i in reversed(range(max_rank)):
			for j in range(self._team.get_num_rankers(i)):
					strategic_point = opening_points[st_idx]
					position = self._map_manager.get_strategic_point(strategic_point)
					self.__opening_positions[(i, j)] = position
					# print('Opening position:', str(position))
					st_idx += 1
					