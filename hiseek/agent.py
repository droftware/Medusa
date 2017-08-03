from abc import ABCMeta, abstractmethod
import copy
import random

import percept
import message
import coord
import action
import controller
import planner
import vector

class AgentType:
	Hider = 0
	Seeker = 1

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
		self._prev_position = None	
		self._stop_counter = 0

	def set_percept(self, percept):
		'''
			Simulator sets the current percept of the agent
		'''
		self._percept = percept

	def get_percept(self):
		'''
			Returns the current percept
		'''
		return self._percept

	def set_position(self, coordinate):
		'''
			Simulator accepts the chosen action from the agent and updates the
			current position accordingly
		'''
		# if self._position != None:
		# 	print('Distance moved:', self._position.get_euclidean_distance(coordinate))
		if self._position == self._prev_position:
			self._stop_counter += 1
		else:
			self._stop_counter = 0
		self._prev_position = self._position
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

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def select_action(self):
		self._action = random.choice(action.Action.all_actions)

	def clear_temporary_state(self):
		pass


class RandomSeekerAgent(SeekerAgent):
	'''
		A seeker which takes a random move each turn
	'''

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def select_action(self):
		# print('Position:', str(self._position))
		# print('Action:', self._action)
		# print('\n')
		self._action = random.choice(action.Action.all_actions)
		# print('Seekers position:', str(self._position))

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
					position = coord.Coord(random.randint(0, gamemap.get_map_width()), random.randint(0, gamemap.get_map_height()))
					within_obstacle = self.__check_within_obstacle(position)
					already_occupied = self.__check_already_occupied(position)
					if not within_obstacle and not already_occupied:
						self.__opening_positions[(i, j)] = position
						found_position = True



class BayesianHiderAgent(HiderAgent):

	def __init__(self, agent_id, team, map_manager):
		super(BayesianHiderAgent, self).__init__(agent_id, team, map_manager)
		self.__controller = controller.BayesianCuriousController(map_manager, AgentType.Hider)
		self.__in_transit = False
		self.__next_state = None
		self.__planner = planner.BasicPlanner(self._map_manager)
		self.__margin = 40

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def __select_path(self):
		start_coord = self._position
		goal_coord = coord.Coord(60, 60)
		self.__planner.plan(start_coord, goal_coord)
		# self.__planner.plan_random_goal(start_coord)

	def __select_direction(self):
		if self.__in_transit:
			# print('Next state:', str(self.__next_state))

			# Decides wether the next_state needs to change or not
			if self._position.get_euclidean_distance(self.__next_state) <= self.__margin:
				# print('!! Reached the next state, finding next state ...')
				self.__next_state = self.__planner.get_paths_next_coord()
				if self.__next_state == None:
					# Agent reached its destination

					# print(' Goal reached !!! , no appropriate Next state')
					self.__in_transit = False

			# If the next state is vaid, calculate the vector and return
			if self.__next_state != None:
				# print(' next state is valid, finding and returning the direction vec ...')
				direction_vec = vector.Vector2D.from_coordinates(self.__next_state, self._position)
				direction_vec.normalize()
				return direction_vec

		# print('Returning None')
		return None

	def __select_closest_action(self, direction_vec):
		max_cos_prod = -1 * float('inf')
		max_action = 0
		# print('*** Selecting action')
		for i in range(action.Action.num_actions):
			if i == action.Action.ST:
				continue
			action_vec = action.VECTOR[i]
			action_vec.normalize()
			direction_vec.normalize()
			cos_prod = direction_vec.dot_product(action_vec)
			# print(' ')
			# print('direction vector:', str(direction_vec))
			# print('action vector:', str(action_vec))
			# print('Current action:', action.Action.action2string[i])
			# print('Current cos prod:', cos_prod)
			# print('Existing min cos prod:', max_cos_prod)
			# print('Existing min action:', max_action)
			# if cos_prod < 0:
			# 	continue
			if cos_prod >= max_cos_prod:
				# print('Changing min')
				max_cos_prod = cos_prod
				max_action = i
		# print('Action choosen:', action.Action.action2string[max_action])
		return max_action

	def select_action(self):
		# print(' ')

		if not self.__in_transit:
			if True or self._percept.are_hiders_visible() or self._percept.are_seekers_visible():
				# print('!! Deciding a path')
				self.__select_path()
				self.__next_state = self.__planner.get_paths_next_coord()
				if self.__next_state != None:
					# print('!! Path is valid')
					self.__in_transit = True
				else:
					# print('!! Path is not valid')
					self.__in_transit = False
		# print('Current position:', str(self._position))

		direction_vec = self.__select_direction()
		# print('Direction vec:', str(direction_vec))

		self.__controller.set_current_state(self._position, self._percept, direction_vec)
		if self._stop_counter >= 3:
			self._action = random.choice(action.Action.all_actions)
		else:
			self._action = self.__controller.infer_action()

		# if direction_vec == None:
		# 	self._action = random.choice(action.Action.all_actions)
		# else:
		# 	if self._stop_counter >= 3:
		# 		self._action = random.choice(action.Action.all_actions)
		# 	else:
		# 		self._action = self.__select_closest_action(direction_vec)


	def clear_temporary_state(self):
		pass

class BayesianHiderCommanderAgent(BayesianHiderAgent):

	def __init__(self, agent_id, team, map_manager):
		super(BayesianHiderCommanderAgent, self).__init__(agent_id, team, map_manager)
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


class PlannerSeekerAgent(SeekerAgent):

	def __init__(self, agent_id, team, map_manager):
		super(PlannerSeekerAgent, self).__init__(agent_id, team, map_manager)
		self.__in_transit = False
		self.__next_state = None
		self.__planner = planner.BasicPlanner(self._map_manager)


	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def __select_path(self):
		start_coord = self._position
		# goal_coord = self._percept.get_hiders()[0]
		self.__planner.plan_random_goal(start_coord)

	def __select_direction(self):
		self._action = random.choice(action.Action.all_actions)

	def select_action(self):
		# print('Current position', str(self._position))
		if not self.__in_transit and self._percept.are_hiders_visible():
			print('*** Hiders visible')
			self.__select_path()
			self.__select_direction()
		else:
			self.__select_direction()


	def clear_temporary_state(self):
		pass


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
