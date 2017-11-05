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
		# print('Position set:', str(self._position))
		


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


class UCBAggressiveAgent(Agent):
	'''
		An agent which uses stochastic UCB to select strategic points
	'''

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBAggressiveAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__planner = planner.BasicPlanner(self._map_manager)
		self.__margin = 8
		self.__next_state = None
		self.__num_rows = self._map_manager.get_num_rows()
		self.__num_cols = self._map_manager.get_num_cols()
		self.__max_cells_visible = self._map_manager.get_max_cells_visible()
		self.__offset = self._map_manager.get_offset()
		self.__micro_actions = [action.Action.NW, action.Action.N, action.Action.NE, action.Action.W, action.Action.E, action.Action.SW, action.Action.S, action.Action.SE]
		self.__num_strategic_points = self._map_manager.get_num_strategic_points()
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		# print('Total number of strategic points:', self.__num_strategic_points)
		self.__macro_UCB = ucb.UCB(self.__num_strategic_points)
		self.__macro_hider_observed = False

		self.__current_st_point = None

		self.__in_long_transit = False
		self.__exploratory_steps = 0
		self.__MAX_EXPLORATORY_STEPS = 5

		self.__in_short_transit = False
		self.__micro_UCB = {}
		self.__micro_idx2cell = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
		self.__micro_chosen_idx = None
		self.__micro_hider_observed = False


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
		# If the next state is vaid, calculate the vector and return
		if self._position != self.__next_state and self.__next_state != None:
			# print(' next state is valid, finding and returning the direction vec ...')
			direction_vec = vector.Vector2D.from_coordinates(self.__next_state, self._position)
			direction_vec.normalize()
			return direction_vec
		
		return None

	def __initiate_long_transit(self):
		self.__exploratory_steps = self.__MAX_EXPLORATORY_STEPS
		self.__in_short_transit = False
		print('S: Select action')
		self.__current_st_point = self.__macro_UCB.select_action()
		print('S: Strategic point selected:', self.__current_st_point)
		self.__select_path(self.__current_st_point)
		self.__next_state = self.__planner.get_paths_next_coord()
		print('S Starting Long transit from:', str(self._position))
		print('S Next state:', str(self.__next_state))
		if self.__next_state != None:
			print('S long transits path is valid')
			self.__in_long_transit = True
		else:
			print('S long transits path is NOT valid')
			self.__in_long_transit = False

	def __update_long_transit(self):
		if self._percept.are_hiders_visible():
			closest_st_point = self._map_manager.get_closest_strategic_point(self._position)
			closest_st_point = closest_st_point[0]
			macro_reward = 10
			self.__macro_UCB.update(closest_st_point, macro_reward)	
			print('S Hider visible during long transit')
			print('S Updating macro UCB for st pt:', closest_st_point)

				# Decides wether the next_state needs to change or not
		if self._position.get_euclidean_distance(self.__next_state) <= self.__margin:
			self.__next_state = self.__planner.get_paths_next_coord()
			print('S State reached, changing to next state:', str(self.__next_state))
			if self.__next_state == None:
				# Agent reached its destination
				print('S Long transit completed')
				self.__in_long_transit = False

	def __update_short_transit(self):
		
		if self._percept.are_hiders_visible():
			# print('# Hider visible during short transit')
			self.__macro_hider_observed = True
			self.__micro_hider_observed = True
		if self.__exploratory_steps == 0:
			print('S Exploration around strategic point', self.__current_st_point, 'completed')
			if self.__macro_hider_observed == True:
				macro_reward = 10
				print('S Since hider was observed, macro reward:', macro_reward)
				self.__macro_hider_observed = False
			else:
				macro_reward = -5
				print('S Since hider was NOT observed, macro reward:', macro_reward)

			print('S Updating macro UCB for st pt:', self.__current_st_point)
			self.__macro_UCB.update(self.__current_st_point, macro_reward)

		if self._position.get_euclidean_distance(self.__next_state) <= self.__margin:
			print('S Short transit completed')
			self.__in_short_transit = False
			self.__next_state = None

			if self.__micro_hider_observed == True:
				micro_reward = 10
				self.__micro_hider_observed = False
				# print('# Since hider was observed, micro reward:', micro_reward)
			else:
				micro_reward = -5
				# print('# Since hider was NOT observed, micro reward:', micro_reward)
			# print('# Updating micro UCB for cell:', self.__micro_current_cell, 'for chosen idx:', self.__micro_chosen_idx)
			# print()
			self.__micro_UCB[self.__micro_current_cell].update(self.__micro_chosen_idx, micro_reward)


	def __initiate_short_transit(self):
		# print()
		print('S Starting short transit from', str(self._position), '#Exploratory steps:', self.__exploratory_steps)
		self.__micro_current_cell = self._map_manager.get_cell_from_coord(self._position)
		if self.__micro_current_cell not in self.__micro_UCB:
			self.__create_micro_UCB_entry(self.__micro_current_cell)
		self.__micro_chosen_idx = self.__micro_UCB[self.__micro_current_cell].select_action()
		a, b = self.__micro_idx2cell[self.__micro_chosen_idx]
		x = int((self.__micro_current_cell[0] + a) * self.__offset - self.__offset/2)
		y = int((self.__micro_current_cell[1] + b) * self.__offset - self.__offset/2)
		self.__next_state = coord.Coord(x, y)
		# print('Obstacle Collision:', self._map_manager.get_blockage_value(self.__next_state))
		# print('# Next state set:', str(self.__next_state),'Euclidean distance:',self._position.get_euclidean_distance(self.__next_state))
		self.__in_short_transit = True
		self.__micro_hider_observed = False


	def __update_exploration(self):
		# print('$$ Exploratory steps:', self.__exploratory_steps)
		if not self.__in_long_transit:
			if self.__exploratory_steps == 0:
				self.__initiate_long_transit()
			else:
				self.__exploratory_steps -= 1
				if not self.__in_short_transit:
					self.__initiate_short_transit()
				self.__update_short_transit()

		elif self.__in_long_transit:
			self.__update_long_transit()


	def __create_micro_UCB_entry(self, cell):
		row = cell[0]
		col = cell[1]
		# print('# Creating micro UCB for:', row, col)
		self.__micro_UCB[(row, col)] = ucb.UCB(8)
		factor = [-1, 0, 1]
		act_idx = 0

		for i in factor:
			for j in factor:
				if i == 0 and j == 0:
					continue
				postn = self._map_manager.get_coord_from_cell(row + i, col + j)
				avg_val = 0
				if self._map_manager.get_blockage_value(postn):
					avg_val = 0
				else:
					act = self.__micro_actions[act_idx]
					rotn = action.ROTATION[act]
					vpolygon = self._map_manager.get_visibility_polygon(postn, rotn, self.__num_rays, self.__visibility_angle)
					common_cells = self._map_manager.get_nearby_visibility_cells(postn)
					visible_cells = 0
					for a, b in common_cells:
						coord_obs = coord.Coord(a * self.__offset, b * self.__offset)
						if vpolygon.is_point_inside(coord_obs):
							visible_cells += 1
					if visible_cells == 0:
						visible_cells = 1
					avg_val = self.__max_cells_visible * 1.0/ visible_cells
				# print('For idx:', act_idx, 'avg value:', avg_val)
				self.__micro_UCB[(row, col)].set_initial_average(act_idx, avg_val)
				act_idx += 1
		self.__micro_UCB[(row, col)].set_initial_bounds()
		# print('Micro UCB:',row,col,str(self.__micro_UCB[(row, col)]))
				

	def select_action(self):
		
		self.__update_exploration()
		direction_vec = self.__select_direction() 

		if direction_vec == None:
			# print('@ Direction vec is None, action chosen randomly')
			self._action = random.choice(action.Action.all_actions)
		else:
			if self._stop_counter >= 3:
				# print('@ Agent got stuck, action chosen randomly')
				self._action = random.choice(action.Action.all_actions)
			else:
				self._action = self.__select_closest_action(direction_vec)

	def clear_temporary_state(self):
		pass



class UCBAggressiveCommanderAgent(UCBAggressiveAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBAggressiveCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager, num_rays, visibility_angle)
		# self.__skill = skill.RandomOpeningSkill(agent_type, team, map_manager)
		self.__skill = skill.LineOpeningSkill(agent_type, team, map_manager)
		

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)


class UCBPassiveAgent(Agent):
	'''
		An agent which uses stochastic UCB to select strategic points
	'''

	def __init__(self, agent_type, agent_id, team, map_manager, macro_UCB, num_rays, visibility_angle):
		super(UCBPassiveAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__planner = planner.BasicPlanner(self._map_manager)
		self.__margin = 10
		self.__next_state = None

		self.__macro_UCB = macro_UCB
		self.__macro_seeker_observed = False

		self.__current_st_point = None

		self.__in_transit = False
		self.__waiting_steps = 0
		self.__MAX_WAITING_STEPS = 10
		self.__ST_CONSIDERATION = 4 #Nearest st pts to consider during UCB st point selection

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
		# If the next state is vaid, calculate the vector and return
		if self._position != self.__next_state and self.__next_state != None:
			# print(' next state is valid, finding and returning the direction vec ...')
			# print('Next state:', str(self.__next_state), 'Current position:', str(self._position))
			direction_vec = vector.Vector2D.from_coordinates(self.__next_state, self._position)
			# print('Direction vec:', str(direction_vec))
			direction_vec.normalize()
			return direction_vec
		
		return None

	def __initiate_transit(self):
		print()
		# print('H Initiating transit')
		self.__waiting_steps = self.__MAX_WAITING_STEPS
		possible_strategic_points = self._map_manager.get_closest_strategic_point(self._position, self.__ST_CONSIDERATION + 1)
		# print('Strategic points under consideration:', possible_strategic_points)
		if self.__current_st_point in possible_strategic_points:
			possible_strategic_points.remove(self.__current_st_point)
		# print('Strategic points after elimination', possible_strategic_points)
		# print('Current strategic point:', self.__current_st_point)
		self.__current_st_point = self.__macro_UCB.get_greatest_actions(1, possible_strategic_points)[0]
		# print('New strategic point:', self.__current_st_point)

		self.__select_path(self.__current_st_point)
		self.__next_state = self.__planner.get_paths_next_coord()
		# print('* Starting Long transit from:', str(self._position))
		# print('* Next state:', str(self.__next_state))
		if self.__next_state != None:
			# print('* long transits path is valid')
			self.__in_transit = True
		else:
			# print('* long transits path is NOT valid')
			self.__in_transit = False
		# print('H Current state', str(self._position),'Next state:', str(self.__next_state))

	def __update_transit(self):
		# print('H Update transit, current position:', str(self._position))
		if self._percept.are_seekers_visible():
			closest_st_point = self._map_manager.get_closest_strategic_point(self._position)
			closest_st_point = closest_st_point[0]
			macro_reward = -20
			self.__macro_UCB.update(closest_st_point, macro_reward)
			# print('H Seekers are visible updating st pt', closest_st_point,' with reward:', macro_reward)
			# print('H Hider UCB Status:', str(self.__macro_UCB))


				# Decides wether the next_state needs to change or not
		if self._position.get_euclidean_distance(self.__next_state) <= self.__margin:
			# print('H Reached target ')
			self.__next_state = self.__planner.get_paths_next_coord()
			if self.__next_state == None:
				# Agent reached its destination
				# print('* Long transit completed')
				self.__in_transit = False


	def __update_waiting(self):
		# print('H Waiting...(update)')
		self.__waiting_steps -= 1
		if self._transit_trigger_condition():
			if self._percept.are_seekers_visible():
				macro_reward = -20
				# print('H Seeker visible, macro reward:', macro_reward)

			elif self.__waiting_steps == 0:
				macro_reward = -10
			# 	print('H Waiting steps ended, since no seeker visible, updating UCB at', self.__current_st_point ,'with reward:', macro_reward)
			# print('H Updating macro UCB for st point:', self.__current_st_point)
			self.__macro_UCB.update(self.__current_st_point, macro_reward)
			# print('H Hider UCB Status:', str(self.__macro_UCB))

	def _transit_trigger_condition(self):
		if self.__waiting_steps == 0 or self._percept.are_seekers_visible():
			return True
		else:
			return False

	def __update_exploration(self):
		# print('$$ Waiting steps:', self.__waiting_steps)
		if not self.__in_transit:
			if self._transit_trigger_condition():
				self.__initiate_transit()
			elif self.__waiting_steps > 0:
				self.__update_waiting()
		elif self.__in_transit:
			self.__update_transit()

	def select_action(self):
		
		self.__update_exploration()
		direction_vec = self.__select_direction() 


		if direction_vec == None:
			# print('@ Direction vec is None, action chosen randomly')
			self._action = random.choice(action.Action.all_actions)
			# if self._position != self.__next_state:
				# self._action = random.choice(action.Action.all_actions)
			# else:
				# self.action = action.Action.ST
		else:
			if self._stop_counter >= 3:
				# print('@ Agent got stuck, action chosen randomly')
				self._action = random.choice(action.Action.all_actions)
			else:
				self._action = self.__select_closest_action(direction_vec)

	def clear_temporary_state(self):
		pass

class UCBPassiveCommanderAgent(UCBPassiveAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, macro_UCB, num_rays, visibility_angle):
		super(UCBPassiveCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager, macro_UCB, num_rays, visibility_angle)
		self.__skill = skill.UCBOpeningSkill(agent_type, team, map_manager, macro_UCB, randomOpening=True)

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)


class UCBCoverageAgent(Agent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBCoverageAgent, self).__init__(agent_type, agent_id, team, map_manager)
		self.__planner = planner.BasicPlanner(self._map_manager)
		self.__margin = 8
		self.__next_state = None
		
		self.__offset = self._map_manager.get_offset()
		self.__micro_actions = [action.Action.NW, action.Action.N, action.Action.NE, action.Action.W, action.Action.E, action.Action.SW, action.Action.S, action.Action.SE]
		self.__num_coverage_points = self._map_manager.get_num_coverage_points()
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		# print('Total number of strategic points:', self.__num_strategic_points)
		self._coverage_UCB = ucb.UCB(self.__num_coverage_points)
		self.__hider_observed = False

		self._current_coverage_point = None
		self.__current_coverage_contour = None

		self.__in_change_transit = False
		self.__in_contour_transit = False

		self.__in_scan_state = False
		self.__scan_counter = 0
		self.__scan_directions = [action.Action.N, action.Action.S, action.Action.E, action.Action.W]

		self.__contour_counter = 0
		self.__contour_size = 0

		self.__seen_reward = 10
		self.__unseen_reward = -4


	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

	def set_initial_coverage_point(self, coverage_point):
		self.__set_contour_path(coverage_point)
		
	def __select_path(self, coverage_point):
		start_coord = self._position
		goal_coord = self._map_manager.get_coverage_point(coverage_point)
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
		# If the next state is vaid, calculate the vector and return
		if self._position != self.__next_state and self.__next_state != None:
			# print(' next state is valid, finding and returning the direction vec ...')
			# print('Next state:', str(self.__next_state), 'Current position:', str(self._position))
			direction_vec = vector.Vector2D.from_coordinates(self.__next_state, self._position)
			# print('Direction vec:', str(direction_vec))
			direction_vec.normalize()
			return direction_vec
		
		return None

	def _get_max_coverage_point(self):
		max_coverage_point = self._coverage_UCB.select_action()
		return max_coverage_point

	def _update_coverage_UCB(self, coverage_point, reward):
		self._coverage_UCB.update(coverage_point, reward)

	def __set_contour_path(self, coverage_point):
		self.__current_coverage_contour = self._map_manager.get_coverage_contour_from_point(coverage_point)
		self.__contour_counter = 0
		self.__contour_size = len(self.__current_coverage_contour)
		self._current_coverage_point = self.__current_coverage_contour[self.__contour_counter]
		print('Agent ID:', self._id, 'S: Setting a new contour:', self.__current_coverage_contour)
		# print('S: Coverage point selected:', self._current_coverage_point)
		self.__select_path(self._current_coverage_point)
		self.__next_state = self.__planner.get_paths_next_coord()
		# print('S Starting Long contour transit from:', str(self._position))
		# print('S Next state:', str(self.__next_state))
		if self.__next_state != None:
			# print('S long transits path is valid')
			self.__in_change_transit = True
		else:
			# print('S long transits path is NOT valid')
			self.__in_change_transit = False


	def __initiate_change_transit(self):
		# self.__in_contour_transit = False
		# print()
		# print('S: Inititating change transit')
		max_coverage_point = self._get_max_coverage_point()
		if max_coverage_point == None:
			return
		self.__set_contour_path(max_coverage_point)
		

	def __update_transit(self):
		if self._percept.are_hiders_visible():
			closest_coverage_point = self._map_manager.get_closest_coverage_point(self._position)
			closest_coverage_point = closest_coverage_point[0]
			print('Agent ID:', self._id, 'S: *** Hider visible during transit')
			# print('Agent ID:', self._id, 'S: Updating UCB for coverages pt:', closest_coverage_point)
			self._update_coverage_UCB(closest_coverage_point, self.__seen_reward)
			
		# Decides wether the next_state needs to change or not
		if self._position.get_euclidean_distance(self.__next_state) <= self.__margin:
			self.__next_state = self.__planner.get_paths_next_coord()
			# print('S State reached, changing to next state:', str(self.__next_state))
			if self.__next_state == None:
				# Agent reached its destination
				# print('S Change transit completed')
				self.__in_scan_state = True
				self.__scan_counter = 0
				if self.__in_change_transit:
					print('Agent ID:', self._id ,'S: Change transit completed')
					self.__in_change_transit = False
				elif self.__in_contour_transit:
					print('Agent ID:', self._id ,'S: Contour transit completed')
					self.__in_contour_transit = False

	def __initiate_contour_transit(self):
		print()
		print('Agent ID:', self._id ,'S: Initiating contour transit')
		print('Agent ID:', self._id ,'S: Contour counter:', self.__contour_counter)
		self._current_coverage_point = self.__current_coverage_contour[self.__contour_counter]
		# print('S: Coverage point selected:', self._current_coverage_point)
		self.__select_path(self._current_coverage_point)
		self.__next_state = self.__planner.get_paths_next_coord()
		# print('S Starting contour transit from:', str(self._position))
		# print('S Next state:', str(self.__next_state))
		if self.__next_state != None:
			# print('S long transits path is valid')
			self.__in_contour_transit = True
		else:
			# print('S long transits path is NOT valid')
			self.__in_contour_transit = False

	def __update_scan(self):
		# print()
		# print('Agent ID:', self._id, 'S: Updating scan')
		if self._percept.are_hiders_visible():
			print('Agent ID:', self._id ,'S: Hider observed during scan')
			self.__hider_observed = True

		self.__scan_counter += 1
		# print('S: Incrementing scan counter')

		if self.__scan_counter == 4:
			reward = 0
			if self.__hider_observed:
				print('Agent ID:', self._id, 'S: Scan completed, updating with a positive reward')
				reward = self.__seen_reward
			else:
				print('Agent ID:', self._id, 'S: Scan completed, updating with a negative reward')
				reward = self.__unseen_reward
			self.__hider_observed = False
			self.__in_scan_state = False
			self.__contour_counter += 1
			self._update_coverage_UCB(self._current_coverage_point, reward)

	def _transit_trigger_condition(self):
		return self.__contour_counter == self.__contour_size

	def __update_exploration(self):
		if self.__in_scan_state:
			self.__update_scan()
		else:
			if not self.__in_change_transit:
				if self._transit_trigger_condition():
					self.__initiate_change_transit()
				else:
					if not self.__in_contour_transit:
						self.__initiate_contour_transit()
			if self.__in_change_transit or self.__in_contour_transit:
				self.__update_transit()

	def select_action(self):
		# print('')
		# print('Agent id:', self._id)
		
		self.__update_exploration()

		if self.__in_scan_state:
			self._action = self.__scan_directions[self.__scan_counter]
		else:
			direction_vec = self.__select_direction() 
			if direction_vec == None:
				# print('@ Direction vec is None, action chosen randomly')
				self._action = random.choice(action.Action.all_actions)
				# if self._position != self.__next_state:
					# self._action = random.choice(action.Action.all_actions)
				# else:
					# self.action = action.Action.ST
			else:
				if self._stop_counter >= 3:
					# print('@ Agent got stuck, action chosen randomly')
					self._action = random.choice(action.Action.all_actions)
				else:
					self._action = self.__select_closest_action(direction_vec)

	def clear_temporary_state(self):
		pass


class UCBCoverageCommanderAgent(UCBCoverageAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBCoverageCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager, num_rays, visibility_angle)
		self.__skill = skill.RandomOpeningSkill(agent_type, team, map_manager)

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)	

	def generate_messages(self):
		pass

	def analyze_messages(self):
		pass

class UCBCoverageCommunicationAgent(UCBCoverageAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBCoverageCommunicationAgent, self).__init__(agent_type, agent_id, team, map_manager, num_rays, visibility_angle)
		self.__content = None
		self.__commander_id = 0
		self.__max_coverage_point = None


	def generate_messages(self):
		# print('Generating message:', self.__content)
		self._agent_messenger.compose(self.__commander_id, self.__content)

	def analyze_messages(self):
		print()
		print('Agent ID:', self._id ,'Agent: analyzing messages')
		messages = self._agent_messenger.get_new_messages()
		assert(len(messages) <= 1)
		if len(messages) == 1:
			content = messages[0].get_content().strip()
			print('Agent ID:', self._id ,'Agent: Message content:', content)
			if content[0] == 'T':
				self.__max_coverage_point = int(content.split(',')[1])
			else:
				self.__max_coverage_point = None
		else:
			self.__max_coverage_point = None

	def _get_max_coverage_point(self):
		self.analyze_messages()
		return self.__max_coverage_point

	def _update_coverage_UCB(self, coverage_point, reward):
		# print('** Called **')
		type_flag = 'U'
		if self._transit_trigger_condition():
			type_flag = 'L'
		self.__content = type_flag + ', ' + str(coverage_point) + ', ' + str(reward)
		print('Agent ID:', self._id ,'Agent: sending message:', self.__content)
		self.generate_messages()


class UCBCoverageCommunicationCommanderAgent(UCBCoverageCommanderAgent):

	def __init__(self, agent_type, agent_id, team, map_manager, num_rays, visibility_angle):
		super(UCBCoverageCommunicationCommanderAgent, self).__init__(agent_type, agent_id, team, map_manager, num_rays, visibility_angle)
		self.__skill = skill.LineOpeningSkill(agent_type, team, map_manager)
		self.__stopped_agents = []
		self.__stopped_contours = []

		self.__num_members = self._team.get_num_agents()
		self.__num_coverage_contours = self._map_manager.get_num_coverage_contours()
		self.__coverage_point_allotments = []

		self.__contour_assignment = [False for i in range(self.__num_coverage_contours)]
		# self.__agent2contour = [None for i in range(self.__num_members)]

		self.__allot_coverage_points()

	def get_opening_position(self, rank, idx):
		return self.__skill.get_opening_position(rank, idx)
 
	def get_opening_coverage_point(self, agent_id):
		return self.__coverage_point_allotments[agent_id]

	def __allot_coverage_points(self):
		replace = False
		if self.__num_members > self.__num_coverage_contours:
			replace = True
		contour_id_allotments = np.random.choice(self.__num_coverage_contours, self.__num_members, replace=replace)
		contour_id_allotments = list(contour_id_allotments)

		agent_id = 0
		for contour_id in contour_id_allotments:
			self.__contour_assignment[contour_id] = True
			# print('Marking:', contour_id, 'as assigned')
			contour = self._map_manager.get_coverage_contour(contour_id)
			coverage_point = contour[0]
			self.__coverage_point_allotments.append(coverage_point)

	def __get_unalloted_coverage_points(self):
		unalloted_coverage_points = []
		for contour_id in range(self.__num_coverage_contours):
			if not self.__contour_assignment[contour_id]:
				contour = self._map_manager.get_coverage_contour(contour_id)
				for coverage_point in contour:
					unalloted_coverage_points.append(coverage_point)
		return unalloted_coverage_points

	def _get_max_coverage_point(self):
		unalloted_coverage_points = self.__get_unalloted_coverage_points()
		num_unalloted_cpoints = len(unalloted_coverage_points)
		coverage_points = None
		if num_unalloted_cpoints < 1:
			coverage_points = self._coverage_UCB.get_greatest_actions(1)
		else:
			coverage_points = self._coverage_UCB.get_greatest_actions(1, unalloted_coverage_points)
		max_coverage_point = coverage_points[0]
		
		# Unmarking previous contour id
		previous_contour_id = self._map_manager.get_coverage_contour_id_from_point(self._current_coverage_point)
		self.__contour_assignment[previous_contour_id] = False

		# Marking current contour id
		current_contour_id = self._map_manager.get_coverage_contour_id_from_point(max_coverage_point)
		self.__contour_assignment[current_contour_id] = True
		return max_coverage_point


	def generate_messages(self):
		# print()
		num_stopped_agents = len(self.__stopped_agents)
		unalloted_coverage_points = self.__get_unalloted_coverage_points()
		num_unalloted_cpoints = len(unalloted_coverage_points)
		coverage_points = None
		if num_unalloted_cpoints < num_stopped_agents:
			coverage_points = self._coverage_UCB.get_greatest_actions(num_stopped_agents)
		else:
			coverage_points = self._coverage_UCB.get_greatest_actions(num_stopped_agents, unalloted_coverage_points)
		for i in range(num_stopped_agents):
			agent_id = self.__stopped_agents[i]
			content = 'T, ' + str(coverage_points[i]) 
			print('Agent ID:', self._id , 'Commander: sending message:', content)
			self._agent_messenger.compose(agent_id, content)

		for coverage_point in coverage_points:
			contour_id = self._map_manager.get_coverage_contour_id_from_point(coverage_point)
			self.__contour_assignment[contour_id] = True
			# print('Marking:', contour_id, 'as assigned')

		for contour_id in self.__stopped_contours:
			self.__contour_assignment[contour_id] = False
			# print('Marking:', contour_id, ' as NOT assigned')

	def analyze_messages(self):
		# print()
		# print('Commander: analyzing messages')
		messages = self._agent_messenger.get_new_messages()
		del self.__stopped_agents[:]
		del self.__stopped_contours[:]
		for mail in messages:
			print('Agent ID:', self._id ,'Commander: Mail:',str(mail),'sender:', mail.get_sender(), 'receiver:', mail.get_receiver())
			content = mail.get_content().strip()
			
			if content[0] == 'U' or content[0] == 'L':
				token = content.split(',')
				coverage_point = int(token[1])
				reward = int(token[2])
				self._update_coverage_UCB(coverage_point, reward)
				print('Agent ID:', self._id ,'Coverage UCB updated')

				if content[0] == 'L':
					sender_id = mail.get_sender()
					self.__stopped_agents.append(sender_id)
					contour_id = self._map_manager.get_coverage_contour_id_from_point(coverage_point)
					self.__stopped_contours.append(contour_id)


	def select_action(self):
		# print('')
		# print('Commander id:', self._id)
		self.analyze_messages()
		self.generate_messages()
		super(UCBCoverageCommunicationCommanderAgent, self).select_action()



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
