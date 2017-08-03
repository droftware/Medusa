from abc import ABCMeta, abstractmethod

import random

import coord

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