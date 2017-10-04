from abc import ABCMeta, abstractmethod
import copy
import random
import math

import numpy as np

import percept
import message
import coord
import action
import controller
import planner
import vector
import skill
import ucb

class AgentType(object):
	Hider = 0
	Seeker = 1

class Agent(object):
	'''
		An abstract base class describing the general agent functionality.
	'''

	__metaclass__ = ABCMeta


	def __init__(self, agent_type, agent_id, team, map_manager):
		self._agent_type = agent_type
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


class RandomAgent(Agent):
	'''
		An agent which takes a random move each turn
	'''

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def select_action(self):
		self._action = random.choice(action.Action.all_actions)

	def clear_temporary_state(self):
		pass


class RandomCommanderAgent(RandomAgent):

	def __init__(self, agent_type, agent_id, team, map_manager):
		super(RandomCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__skill = skill.RandomOpeningSkill(agent_type, team, map_manager)

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)


class BayesianAgent(Agent):

	def __init__(self, agent_type, agent_id, team, map_manager):
		super(BayesianAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__controller = controller.BayesianMobileController(map_manager, agent_type)
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

class BayesianCommanderAgent(BayesianAgent):

	def __init__(self, agent_type, agent_id, team, map_manager):
		super(BayesianCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__skill = skill.RandomOpeningSkill(agent_type, team, map_manager)

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)


class PlannerAgent(Agent):

	def __init__(self, agent_type, agent_id, team, map_manager):
		super(PlannerAgent, self).__init__(agent_type, agent_id, team, map_manager)
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


class StochasticBanditAgent(Agent):
	'''
		An agent which uses UCB to select strategic points
	'''

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(StochasticBanditAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__planner = planner.BasicPlanner(self._map_manager)
		self.__margin = 40
		self.__num_rows = self._map_manager.get_num_rows()
		self.__num_cols = self._map_manager.get_num_cols()
		self.__max_cells_visible = self._map_manager.get_max_cells_visible()
		self.__offset = self._map_manager.get_offset()
		self.__micro_actions = [action.Action.NW, action.Action.N, action.Action.NE, action.Action.W, action.Action.E, action.Action.SW, action.Action.S, action.Action.SE]
		self.__num_strategic_points = self._map_manager.get_num_strategic_points()
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		print('Total number of strategic points:', self.__num_strategic_points)
		self.__macro_UCB = ucb.UCB(self.__num_strategic_points)
		self.__macro_hider_observed = False

		self.__current_st_point = None

		self.__in_transit = False
		self.__exploratory_steps = 0

		self.__micro_UCB = {}
		self.__micro_idx2cell = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
		self.__micro_chosen_cell = None


	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def __select_path(self, strategic_point):
		start_coord = self._position
		goal_coord = self._map_manager.get_strategic_point(strategic_point)
		self.__planner.plan(start_coord, goal_coord)
	
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
			
			if cos_prod >= max_cos_prod:
				# print('Changing min')
				max_cos_prod = cos_prod
				max_action = i
		# print('Action choosen:', action.Action.action2string[max_action])
		return max_action

	def __select_direction(self):
		if self.__in_transit:
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
		else:
			if self.__exploratory_steps > 0:

		return None

	def __perform_macro_exploration(self):
		# Perform macro tasks
		if not self.__in_transit:
			if self.__exploratory_steps == 0:
				self.__exploratory_steps = 5
				self.__current_st_point = self.__macro_UCB.select_action()
				self.__select_path(self.__current_st_point)
				self.__next_state = self.__planner.get_paths_next_coord()
				if self.__next_state != None:
					print('!! Path is valid')
					self.__in_transit = True
				else:
					print('!! Path is not valid')
					self.__in_transit = False
			else:
				self.__exploratory_steps -= 1
				if self._percept.are_hiders_visible():
					print('Reward updated NOT during transit')
					self.__macro_hider_observed = True
				if self.__exploratory_steps == 0:
					if self.__macro_hider_observed == True:
						reward = 5
						self.__macro_hider_observed = False
					else:
						reward = -1
					self.__macro_UCB.update(self.__current_st_point, reward)
		if self.__in_transit:
			if self._percept.are_hiders_visible():
				print('Reward updated during transit')
				closest_st_point = self._map_manager.get_closest_strategic_point(self._position)
				reward = 5	
				self.__macro_UCB.update(closest_st_point, reward)	

		direction_vec = self.__select_direction() 
		return direction_vec

	def __create_micro_UCB_entry(self, row, col):
		self.__micro_UCB[(row, col)] = ucb.UCB(8)
		factor = [-1, 0, 1]
		act_idx = 0

		for i in factor:
			for j in factor:
				if i == 0 and j == 0:
					continue
				x = int((row + i) * self.__offset - self.__offset/2)
				y = int((col + j) * self.__offset - self.__offset/2)
				postn = coord.Coord(x, y)
				act = self.__micro_actions[act_idx]
				
				rotn = action.ROTATION[act]
				vpolygon = self._map_manager.get_visibility_polygon(postn, rotn, self.__num_rays, self.__visibility_angle)
				common_cells = self._map_manager.get_nearby_visibility_cells(postn)
				visible_cells = 0
				for a, b in common_cells:
					coord_obs = coord.Coord(a * self.__offset, b * self.__offset)
					if vpolygon.is_point_inside(coord_obs):
						visible_cells += 1
				avg_val = self.__max_cells_visible * 1.0/ visible_cells
				self.__micro_UCB[(row, col)].set_initial_average(act_idx, avg_val)
				act_idx += 1
				

	def __perform_micro_exploration(self):
		if not self.__in_transit:
			if self.__exploratory_steps > 0:
				print('Performed')
				row = self._position.get_x()*1.0/self._map_manager.get_num_rows()
				col = self._position.get_y()*1.0/self._map_manager.get_num_cols()
				current_cell = (row, col)
				if current_cell not in self.__micro_UCB:
					self.__create_micro_UCB_entry(row, col)
				chosen_idx = self.__micro_UCB[(row, col)].select_action()
				a, b = self.__micro_idx2cell[chosen_idx]
				# self.__micro_chosen_cell = (row + a, col + b)
				x = int((row + a) * self.__offset - self.__offset/2)
				y = int((col + b) * self.__offset - self.__offset/2)
				self.__next_state = coord.Coord(x, y)




		# if self.__micro_chosen_cell != None and current_cell != self.__micro_chosen_cell:
			


	def select_action(self):
		
		direction_vec = self.__perform_macro_exploration()

		if direction_vec == None:
			print('Performing micro exploration')
			direction_vec = self.__perform_micro_exploration()

		# print('Seeker position:', str(self._position))

		if direction_vec == None:
			# print('Direction vec is None')
			self._action = random.choice(action.Action.all_actions)
		else:
			if self._stop_counter >= 3:
				self._action = random.choice(action.Action.all_actions)
			else:
				self._action = self.__select_closest_action(direction_vec)

	def clear_temporary_state(self):
		pass



class StochasticBanditCommanderAgent(StochasticBanditAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(StochasticBanditCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager, num_rays, visibility_angle)
		self.__skill = skill.RandomOpeningSkill(agent_type, team, map_manager)

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)



# class FidgetingAgent(Agent):
# 	'''
# 		A hider agent which takes a random action on seeing a seeker. It also 
# 		communicates this fact(sighting of a seeker) to all its fellow hiders.
# 	'''
# 	def __init__(self, agent_type, agent_id, team, map_manager):
# 		super(FidgetingAgent, self).__init__(agent_type, agent_id, team, map_manager)
# 		self.__seeker_spotted = False

# 	def generate_messages(self):
# 		if self._percept.are_seekers_visible():
# 			self._agent_messenger.broadcast('seeker spotted')

# 	def analyze_messages(self):
# 		unread_messages = self._agent_messenger.get_new_messages()
# 		for message in unread_messages:
# 			if message.get_content() == 'seeker spotted':
# 				self.__seeker_spotted = True

# 	def select_action(self):
# 		if self.__seeker_spotted or self._percept.are_hiders_visible():
# 			valid_actions = []
# 			available_actions = coord.Coord.get_all_actions()
# 			test_position = copy.deepcopy(self._position)
# 			for move in available_actions:
# 				test_position.move_action(move)
# 				if self._map_manager.is_inside(test_position):
# 					if not self._map_manager.is_obstacle(test_position):
# 						valid_actions.append(move)
# 				test_position.revert_action()

# 			if valid_actions:
# 				self._action = random.choice(valid_actions)
# 			else:
# 				self._action = None
# 		else:
# 			self._action = None

# 	def clear_temporary_state(self):
# 		self.__seeker_spotted = False
