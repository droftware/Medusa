import pomegranate as pm

import coord
import percept
import action

class BayesianController(object):

	def __init__(self, map_manager):
		self.__map_manager = map_manager
		self.__position = None
		self.__percept = None
		self.__action_map = None

		# Random variables of the bayesian network
		# '__r_' stands for random variable
		# self.__objective = [None] * action.Action.num_actions
		self.__r_danger = [None] * action.Action.num_actions
		self.__r_obstruction = [None] * action.Action.num_actions
		self.__r_visibility = [None] * action.Action.num_actions
		self.__r_hider = [None] * action.Action.num_actions
		self.__r_seeker = [None] * action.Action.num_actions
		self.__r_blockage = [None] * action.Action.num_actions

		# Probability distributions
		# '__d_' stands for discrete distributions

		self.__d_direction = [pm.DiscreteDistribution({'T':0.5, 'F':0.5}) for i in range(action.Action.num_actions)]

		self.__d_danger = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.99],
					 ['T', '1', 0.01],
					 ['F', '0', 0.5],
					 ['F', '1', 0.5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		self.__d_visibility = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.01],
					 ['T', '1', 0.03],
					 ['T', '2', 0.06],
					 ['T', '3', 0.2],
					 ['T', '4', 0.7],
					 ['F', '0', 1./5],
					 ['F', '1', 1./5],
					 ['F', '2', 1./5],
					 ['F', '3', 1./5],
					 ['F', '4', 1./5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		self.__d_obstruction = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.01],
					 ['T', '1', 0.03],
					 ['T', '2', 0.06],
					 ['T', '3', 0.2],
					 ['T', '4', 0.7],
					 ['F', '0', 1./5],
					 ['F', '1', 1./5],
					 ['F', '2', 1./5],
					 ['F', '3', 1./5],
					 ['F', '4', 1./5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		self.__d_hider = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.9],
					 ['T', '1', 0.066],
					 ['T', '2', 0.033],
					 ['F', '0', 1./3],
					 ['F', '1', 1./3],
					 ['F', '2', 1./3]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		self.__d_seeker = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.9],
					 ['T', '1', 0.077],
					 ['T', '2', 0.022],
					 ['F', '0', 1./3],
					 ['F', '1', 1./3],
					 ['F', '2', 1./3]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		self.__d_blockage = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.9999],
					 ['T', '1', 0.0001],
					 ['F', '0', 0.5],
					 ['F', '1', 0.5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]

		# State objects(for pomegranate) library which hold both the distribution as well as name
		self.__s_direction = [pm.State(self.__d_direction[i], name='direction_'+str(i)) for i in range(action.Action.num_actions)] 
		self.__s_danger = [pm.State(self.__d_danger[i], name='danger_'+str(i)) for i in range(action.Action.num_actions)]
		self.__s_visibility = [pm.State(self.__d_visibility[i], name='visibility_'+str(i)) for i in range(action.Action.num_actions)] 
		self.__s_obstruction = [pm.State(self.__d_obstruction[i], name='obstruction_'+str(i)) for i in range(action.Action.num_actions)] 
		self.__s_hider = [pm.State(self.__d_hider[i], name='hider_'+str(i)) for i in range(action.Action.num_actions)] 
		self.__s_seeker = [pm.State(self.__d_seeker[i], name='seeker_'+str(i)) for i in range(action.Action.num_actions)] 
		self.__s_blockage = [pm.State(self.__d_blockage[i], name='blockage_'+str(i)) for i in range(action.Action.num_actions)] 

		# Model
		self.__model = pm.BayesianNetwork("Bayesian Controller")

		# Adding the states
		for i in range(action.Action.num_actions):
			self.__model.add_states(self.__s_direction[i])

		for i in range(action.Action.num_actions):
			self.__model.add_states(self.__s_danger[i])
			self.__model.add_states(self.__s_visibility[i])
			self.__model.add_states(self.__s_obstruction[i])
			self.__model.add_states(self.__s_hider[i])
			self.__model.add_states(self.__s_seeker[i])
			self.__model.add_states(self.__s_blockage[i])

		# Creating the network by adding transitions
		for i in range(action.Action.num_actions):
			self.__model.add_transition(self.__s_direction[i], self.__s_danger[i])
			self.__model.add_transition(self.__s_direction[i], self.__s_visibility[i])
			self.__model.add_transition(self.__s_direction[i], self.__s_obstruction[i])
			self.__model.add_transition(self.__s_direction[i], self.__s_hider[i])
			self.__model.add_transition(self.__s_direction[i], self.__s_seeker[i])
			self.__model.add_transition(self.__s_direction[i], self.__s_blockage[i])

		self.__model.bake()

		self.__inferred_results = None
		self.__direction_probs = [None] * action.Action.num_actions
		self.__direction_dist = None

	def set_current_position(self, position):
		assert(isinstance(position, coord.Coord))
		self.__position = position

	def set_current_percept(self, current_percept):
		assert(isinstance(current_percept, percept.TeamPercept))
		self.__percept = current_percept

	def set_current_state(self, position, percept):
		self.set_current_position(position)
		self.set_current_percept(percept)

	def __set_action_map(self):
		self.__action_map = self.__map_manager.get_action_map(self.__position)

	def print_random_var_levels(self):
		# print('Levels of random variables')
		print('Danger:', self.__r_danger)
		print('Obstruction:', self.__r_obstruction)
		print('Visibility:', self.__r_visibility)
		print('Hider:', self.__r_hider)
		print('Seeker:', self.__r_seeker)
		print('Blockage:', self.__r_blockage)

	def infer_action(self):
		self.__set_random_var_levels()
		self.__perform_bayesian_inference()
		self.__extract_direction_probabilities()
		self.__create_direction_distribution()
		return self.sample_action()

	def __set_random_var_levels(self):
		self.__set_action_map()
		self.__set_danger_levels()
		self.__set_obstruction_levels()
		self.__set_visibility_levels()
		self.__set_hider_levels()
		self.__set_seeker_levels()
		self.__set_blockage_levels()
		# print('All random vars set')
		# self.print_random_var_levels()
		


	def __perform_bayesian_inference(self):
		rvar_dict = {}

		# Filling random variables
		for i in range(action.Action.num_actions):
			rvar_dict['danger_' + str(i)] = str(self.__r_danger[i])
			rvar_dict['visibility_' + str(i)] = str(self.__r_visibility[i])
			rvar_dict['obstruction_' + str(i)] = str(self.__r_obstruction[i])
			rvar_dict['hider_' + str(i)] = str(self.__r_hider[i])
			rvar_dict['seeker_' + str(i)] = str(self.__r_seeker[i])
			rvar_dict['blockage_' + str(i)] = str(self.__r_blockage[i])

		# print(rvar_dict)
		self.__inferred_results = self.__model.predict_proba(rvar_dict)
		# print(type(self.__inferred_results[63]))

	def __extract_direction_probabilities(self):
		for i in range(action.Action.num_actions):
			self.__direction_probs[i] = self.__inferred_results[i].probability("T")

		# Normalizing
		sum_dp = sum(self.__direction_probs)
		self.__direction_probs = [float(num)/sum_dp for num in self.__direction_probs]
		# print(self.__direction_probs)

	def __create_direction_distribution(self):
		direction_dict = {}
		for i in range(action.Action.num_actions):
			direction_dict[action.Action.action2string[i]] = self.__direction_probs[i]
		self.__direction_dist = pm.DiscreteDistribution(direction_dict)

	def sample_action(self):
		sampled_action = self.__direction_dist.sample()
		return action.Action.string2action[sampled_action]


	def __set_visibility_levels(self):
		'''
			0,1,2,3,4: 5 visibility levels
			--> Increasing visibility
			(Set in a relative manner)
		'''
		visibility_values = []
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			value = self.__map_manager.get_visibility_value(position)
			visibility_values.append((i, value))
		visibility_values = sorted(visibility_values, key=lambda x: x[1])
		level = 0

		level = -1
		for i in range(action.Action.num_actions):
			if i%2 == 0:
				level += 1
			if visibility_values[i][1] == -1:
				self.__r_visibility[visibility_values[i][0]] = 0
			else:
				self.__r_visibility[visibility_values[i][0]] = level


	def __set_obstruction_levels(self):
		'''
			0,1,2,3,4: 5 obstruction levels
			--> Increasing obstruction
			(Greater the value, lesser is the obstruction)
		'''
		obstruction_values = []
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			value = self.__map_manager.get_obstruction_value(position)
			obstruction_values.append((i, value))
		obstruction_values = sorted(obstruction_values, key=lambda x: x[1], reverse=True)
		level = 0

		level = -1
		for i in range(action.Action.num_actions):
			if i%2 == 0:
				level += 1
			if obstruction_values[i][1] == -1:
				self.__r_obstruction[obstruction_values[i][0]] = 0
			else:
				self.__r_obstruction[obstruction_values[i][0]] = level

	def __set_blockage_levels(self):
		'''
			0,1 : 2 blockage levels
			0: Free
			1: Blocked
		'''
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			if self.__map_manager.get_blockage_value(position):
				self.__r_blockage[i] = 1
			else:
				self.__r_blockage[i] = 0

	def __set_danger_levels(self):
		'''
			0,1 : 2 danger levels
			0: No danger
			1: Danger
		'''
		seekers = self.__percept.get_seekers()
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			self.__r_danger[i] = 0
			for spos in seekers:
				visibility_polygon = self.__map_manager.get_360_visibility_polygon(spos)
				if visibility_polygon.is_point_inside(position):
					self.__r_danger[i] = 1
					break

	def __set_hider_levels(self):
		'''
			0,1,2 : seekers presence levels
			0: Free
			1: Near seeker
			2: Very very near to seeker
		'''
		hiders = self.__percept.get_hiders()
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			self.__r_hider[i] = 0
			min_dist = float('inf')
			for hpos in hiders:
				hider_dist = position.get_euclidean_distance(hpos) 
				if hider_dist < min_dist:
					min_dist = hider_dist
			if min_dist >= 0 and min_dist < 5:
				self.__r_hider[i] = 2
			elif min_dist >= 5 and min_dist < 7:
				self.__r_hider[i] = 1

	def __set_seeker_levels(self):
		'''
			0,1,2 : seekers presence levels
			0: Free
			1: Near seeker
			2: Very very near to seeker
		'''
		seekers = self.__percept.get_seekers()
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			self.__r_seeker[i] = 0
			min_dist = float('inf')
			for spos in seekers:
				seeker_dist = position.get_euclidean_distance(spos) 
				if seeker_dist < min_dist:
					min_dist = seeker_dist
			if min_dist >= 0 and min_dist < 5:
				self.__r_seeker[i] = 2
			elif min_dist >= 5 and min_dist < 7:
				self.__r_seeker[i] = 1


