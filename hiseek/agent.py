from abc import ABCMeta, abstractmethod
import copy
import random

import percept
import message
import coord
import action

class Agent(object):
	'''
		An abstract base class describing the general agent functionality.
	'''

	__metaclass__ = ABCMeta

	def __init__(self, agent_id, team, map_manager):
		self._id = agent_id
		self._team = team
		self._map_manager = map_manager
		self._agent_messenger = team.create_agent_messenger(agent_id)
		self._percept = None
		self._action = None
		self._position = None

	def set_percept(self, percept):
		'''
			Simulator sets the current percept of the agent
		'''
		self._percept = percept

	def set_position(self, coordinate):
		'''
			Simulator accepts the chosen action from the agent and updates the
			current position accordingly
		'''
		self._position = coordinate

	def get_position(self):
		return self._position

	def get_action(self):
		return self._action


	@abstractmethod
	def generate_messages(self):
		'''
			Based on the current percept as well as past messages, generates  as well as
			sends new messages to its fellow agents.
		'''
		pass

	@abstractmethod
	def analyze_messages(self):
		'''
			Analyzes the recent as well as past messages to extract some meaning as well
			as modify its temporary state.
		'''
		pass

	@abstractmethod
	def select_action(self):
		'''
			The agent takes an action based on the current percept as well as temporary
			state which has been affected by prior message analysis
		'''
		pass

	@abstractmethod
	def clear_temporary_state(self):
		'''
			The agent clears its temporary state after choosing its action
		'''
		pass

	@abstractmethod
	def agent_type(self):
		'''
			Returns the type of the agent, hider or seeker.
		'''
		pass

class HiderAgent(Agent):

	__metaclass__ = ABCMeta

	def agent_type(self):
		return 'hider_agent'

class SeekerAgent(Agent):

	__metaclass__ = ABCMeta

	def agent_type(self):
		return 'seeker_agent'


class RandomHiderAgent(HiderAgent):
	'''
		A hider which takes a random move each turn
	'''

	def __init__(self, agent_id, team, map_manager):
		super(RandomHiderAgent, self).__init__(agent_id, team, map_manager)

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def select_action(self):
		available_actions = list(action.Action)
		self._action = random.choice(available_actions)

	def clear_temporary_state(self):
		pass


class RandomSeekerAgent(SeekerAgent):
	'''
		A seeker which takes a random move each turn
	'''

	def __init__(self, agent_id, team, map_manager):
		super(RandomSeekerAgent, self).__init__(agent_id, team, map_manager)

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def select_action(self):
		available_actions = list(action.Action)
		self._action = random.choice(available_actions)

	def clear_temporary_state(self):
		pass

class RandomHiderCommanderAgent(RandomHiderAgent):

	def __init__(self, agent_id, team, map_manager):
		super(RandomHiderCommanderAgent, self).__init__(agent_id, team, map_manager)
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

class RandomSeekerCommanderAgent(RandomSeekerAgent):

	def __init__(self, agent_id, team, map_manager):
		super(RandomSeekerCommanderAgent, self).__init__(agent_id, team, map_manager)
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
			rank_holders = self._team.get_num_rankers(i)
			for j in range(rank_holders):
				found_position = False
				while not found_position:
					x = random.randint(0, gamemap.get_map_width())
					y = random.randint(0, gamemap.get_map_height())
					position = coord.Coord(x, y)
					within_obstacle = self.__check_within_obstacle(position)
					already_occupied = self.__check_already_occupied(position)
					if not within_obstacle and not already_occupied:
						self.__opening_positions[(i, j)] = position
						found_position = True


class FidgetingHiderAgent(HiderAgent):
	'''
		A hider agent which takes a random action on seeing a seeker. It also 
		communicates this fact(sighting of a seeker) to all its fellow hiders.
	'''
	def __init__(self, agent_id, team, map_manager):
		super(FidgetingHiderAgent, self).__init__(agent_id, team, map_manager)
		self.__seeker_spotted = False

	def generate_messages(self):
		if self._percept.are_seekers_visible():
			self._agent_messenger.broadcast('seeker spotted')

	def analyze_messages(self):
		unread_messages = self._agent_messenger.get_new_messages()
		for message in unread_messages:
			if message.get_content() == 'seeker spotted':
				self.__seeker_spotted = True

	def select_action(self):
		if self.__seeker_spotted or self._percept.are_hiders_visible():
			valid_actions = []
			available_actions = coord.Coord.get_all_actions()
			test_position = copy.deepcopy(self._position)
			for move in available_actions:
				test_position.move_action(move)
				if self._map_manager.is_inside(test_position):
					if not self._map_manager.is_obstacle(test_position):
						valid_actions.append(move)
				test_position.revert_action()

			if valid_actions:
				self._action = random.choice(valid_actions)
			else:
				self._action = None
		else:
			self._action = None

	def clear_temporary_state(self):
		self.__seeker_spotted = False
