import random

import pomegranate as pm

import agent
import coord
import percept
import action

class BayesianController(object):
	'''
		If sampling True, choose the action by sampling from the posterior direction distribution
		if False, choose the action with the best posteriror probability.
	'''
	def __init__(self, map_manager, agent_type, sampling=False):
		self.__map_manager = map_manager
		self.__position = None
		self.__percept = None
		self.__action_map = None
		self.__target_threshold = 0.3
		self.__max_prob_dir = None

		# target dot products
		self.__target_dots = [None] * action.Action.num_actions

		# Random variables marked as true will be considered in the bayesian net
		self._considered = {'target':True, 'danger':True, 'obstruction':True, 'visibility':True, 
							'hider':True, 'seeker':True, 'blockage':True}

		if agent_type == agent.AgentType.Seeker:
			self._considered['danger'] = False

		self.__sampling = sampling

		# Probability distributions

		self.__d_direction = [pm.DiscreteDistribution({'T':0.5, 'F':0.5}) for i in range(action.Action.num_actions)]
		self.__s_direction = [pm.State(self.__d_direction[i], name='direction_'+str(i)) for i in range(action.Action.num_actions)] 
		

		# Random vars, probability distributions and state vars of considered variables
		# in the bayesian net
		if self._considered['target']:
			self.__r_target = [None] * action.Action.num_actions
			self.__d_target = [None] * action.Action.num_actions
			self.__s_target = None


		if self._considered['danger']:
			self.__r_danger = [None] * action.Action.num_actions
			self.__d_danger = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.99],
					 ['T', '1', 0.01],
					 ['F', '0', 0.5],
					 ['F', '1', 0.5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_danger = [pm.State(self.__d_danger[i], name='danger_'+str(i)) for i in range(action.Action.num_actions)]

		if self._considered['obstruction']:
			self.__r_obstruction = [None] * action.Action.num_actions
			self.__d_obstruction = [pm.ConditionalProbabilityTable(
					[['T', '0', 0.001],
					 ['T', '1', 0.003],
					 ['T', '2', 0.006],
					 ['T', '3', 0.99],
					 ['F', '0', 1./4],
					 ['F', '1', 1./4],
					 ['F', '2', 1./4],
					 ['F', '3', 1./4]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_obstruction = [pm.State(self.__d_obstruction[i], name='obstruction_'+str(i)) for i in range(action.Action.num_actions)] 
		
		if self._considered['visibility']:
			self.__r_visibility = [None] * action.Action.num_actions
			self.__d_visibility = [pm.ConditionalProbabilityTable(
						[['T', '0', 0.001],
						 ['T', '1', 0.003],
						 ['T', '2', 0.006],
						 ['T', '3', 0.99],
						 ['F', '0', 1./4],
						 ['F', '1', 1./4],
						 ['F', '2', 1./4],
						 ['F', '3', 1./4]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_visibility = [pm.State(self.__d_visibility[i], name='visibility_'+str(i)) for i in range(action.Action.num_actions)] 

		if self._considered['hider']:
			self.__r_hider = [None] * action.Action.num_actions
			self.__d_hider = [pm.ConditionalProbabilityTable(
						[['T', '0', 0.9],
						 ['T', '1', 0.066],
						 ['T', '2', 0.033],
						 ['F', '0', 1./3],
						 ['F', '1', 1./3],
						 ['F', '2', 1./3]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_hider = [pm.State(self.__d_hider[i], name='hider_'+str(i)) for i in range(action.Action.num_actions)] 

		if self._considered['seeker']:
			self.__r_seeker = [None] * action.Action.num_actions
			self.__d_seeker = [pm.ConditionalProbabilityTable(
						[['T', '0', 0.9],
						 ['T', '1', 0.077],
						 ['T', '2', 0.022],
						 ['F', '0', 1./3],
						 ['F', '1', 1./3],
						 ['F', '2', 1./3]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_seeker = [pm.State(self.__d_seeker[i], name='seeker_'+str(i)) for i in range(action.Action.num_actions)] 

		if self._considered['blockage']:
			self.__r_blockage = [None] * action.Action.num_actions
			self.__d_blockage = [pm.ConditionalProbabilityTable(
						[['T', '0', 0.999999],
						 ['T', '1', 0.000001],
						 ['F', '0', 0.5],
						 ['F', '1', 0.5]], [self.__d_direction[i]]) for i in range(action.Action.num_actions)]
			self.__s_blockage = [pm.State(self.__d_blockage[i], name='blockage_'+str(i)) for i in range(action.Action.num_actions)] 

		# State objects(for pomegranate) library which hold both the distribution as well as name
		self.__model = None
		self.__inferred_results = None
		self.__direction_probs = [None] * action.Action.num_actions
		self.__direction_dist = None

	def set_current_position(self, position):
		# assert(isinstance(position, coord.Coord))
		self.__position = position

	def set_current_percept(self, current_percept):
		# assert(isinstance(current_percept, percept.TeamPercept))
		self.__percept = current_percept

	def set_current_target_vec(self, target_vec):
		self.__target_vec = target_vec

	def set_current_state(self, position, percept, target_vec):
		self.set_current_position(position)
		self.set_current_percept(percept)
		self.set_current_target_vec(target_vec)

	def __set_target_probability(self):

		for i in range(action.Action.num_actions):
			if i != action.Action.ST:
				prob_value = 0.5
				if self.__target_vec != None:
					direction_vec = action.VECTOR[i]
					direction_vec.normalize()
					self.__target_vec.normalize()
					dot = self.__target_vec.dot_product(direction_vec)
					self.__target_dots[i] = dot
					prob_value = self.__target_threshold + (1.0 - self.__target_threshold) * max(0, dot)
				self.__d_target[i] = pm.ConditionalProbabilityTable(
					[['T', 'T', prob_value],
					 ['T', 'F', 1.0 - prob_value],
					 ['F', 'T', 0.5],
					 ['F', 'F', 0.5]], [self.__d_direction[i]])
			else:
				self.__target_dots[i] = 0
				self.__d_target[i] = pm.ConditionalProbabilityTable(
					[['T', 'T', 0.5],
					 ['T', 'F', 0.5],
					 ['F', 'T', 0.5],
					 ['F', 'F', 0.5]], [self.__d_direction[i]])

		self.__s_target = [pm.State(self.__d_target[i], name='target_' + str(i)) for i in range(action.Action.num_actions)] 

		
	def __set_bayesian_network(self):

		if self._considered['target']:
			self.__set_target_probability()

		# Model
		self.__model = pm.BayesianNetwork("Bayesian Controller")

		# Adding the direction states
		for i in range(action.Action.num_actions):
			self.__model.add_states(self.__s_direction[i])

		for i in range(action.Action.num_actions):
			if self._considered['target']:
				self.__model.add_states(self.__s_target[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_target[i])

			if self._considered['danger']:
				self.__model.add_states(self.__s_danger[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_danger[i])

			if self._considered['obstruction']:
				self.__model.add_states(self.__s_obstruction[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_obstruction[i])

			if self._considered['visibility']:			
				self.__model.add_states(self.__s_visibility[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_visibility[i])

			if self._considered['hider']:
				self.__model.add_states(self.__s_hider[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_hider[i])

			if self._considered['seeker']:
				self.__model.add_states(self.__s_seeker[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_seeker[i])

			if self._considered['blockage']:
				self.__model.add_states(self.__s_blockage[i])
				self.__model.add_transition(self.__s_direction[i], self.__s_blockage[i])

		self.__model.bake()

	def __set_action_map(self):
		self.__action_map = self.__map_manager.get_action_map(self.__position)

	def print_random_var_levels(self):
		# print('Levels of random variables')
		if self._considered['target']:
			print('Target:', self.__r_target)
		if self._considered['danger']:
			print('Danger:', self.__r_danger)
		if self._considered['obstruction']:
			print('Obstruction:', self.__r_obstruction)
		if self._considered['visibility']:
			print('Visibility:', self.__r_visibility)
		if self._considered['hider']:
			print('Hider:', self.__r_hider)
		if self._considered['seeker']:
			print('Seeker:', self.__r_seeker)
		if self._considered['blockage']:
			print('Blockage:', self.__r_blockage)

	def infer_action(self):
		# if self.__target_vec != None:
		# print('Inferring action')
		self.__set_bayesian_network()
		self.__set_random_var_levels()
		self.__perform_bayesian_inference()
		# print('Bayesian inference performed')
		self.__extract_direction_probabilities()
		self.__create_direction_distribution()
		# print('Direction distribution created')
		# print('Returning sampled action')
		if self.__sampling:
			inferred_action = self.sample_action()
		else:
			inferred_action = self.best_action()
		return inferred_action
	
	def __set_random_var_levels(self):
		self.__set_action_map()
		if self._considered['target']:
			self.__set_target_levels()
		if self._considered['danger']:
			self.__set_danger_levels()
		if self._considered['obstruction']:
			self.__set_obstruction_levels()
		if self._considered['visibility']:
			self.__set_visibility_levels()
		if self._considered['hider']:
			self.__set_hider_levels()
		if self._considered['seeker']:
			self.__set_seeker_levels()
		if self._considered['blockage']:
			self.__set_blockage_levels()

		# print('All random vars set')
		# self.print_random_var_levels()


	def __perform_bayesian_inference(self):
		rvar_dict = {}

		# Filling random variables
		for i in range(action.Action.num_actions):
			if self._considered['target']:
				rvar_dict['target_'+str(i)] = str(self.__r_target[i])
			if self._considered['danger']:
				rvar_dict['danger_' + str(i)] = str(self.__r_danger[i])
			if self._considered['visibility']:
				rvar_dict['visibility_' + str(i)] = str(self.__r_visibility[i])
			if self._considered['obstruction']:
				rvar_dict['obstruction_' + str(i)] = str(self.__r_obstruction[i])
			if self._considered['hider']:
				rvar_dict['hider_' + str(i)] = str(self.__r_hider[i])
			if self._considered['seeker']:
				rvar_dict['seeker_' + str(i)] = str(self.__r_seeker[i])
			if self._considered['blockage']:
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
		max_prob_value = 0
		for i in range(action.Action.num_actions):
			if self.__direction_probs[i] > max_prob_value:
				self.__max_prob_dir = i
				max_prob_value = self.__direction_probs[i]
			direction_dict[action.Action.action2string[i]] = self.__direction_probs[i]
		self.__direction_dist = pm.DiscreteDistribution(direction_dict)

	def sample_action(self):
		sampled_action = self.__direction_dist.sample()
		return action.Action.string2action[sampled_action]
	
	def best_action(self):
		return self.__max_prob_dir

	def __set_target_levels(self):

		cos_products = sorted(self.__target_dots, reverse=True)
		threshold = cos_products[1]
		
		for i in range(action.Action.num_actions):
			if self.__target_dots[i] >= threshold:
				self.__r_target[i] = 'T'
			else:
				self.__r_target[i] = 'F'


	def __set_visibility_levels(self):
		'''
			0,1,2,3: 4 visibility levels
			--> Increasing visibility
			(Set in a relative manner)
		'''
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			level = self.__map_manager.get_visibility_level(position)
			self.__r_visibility[i] = str(level)

	def __set_obstruction_levels(self):
		'''
			0,1,2,3: 4 obstruction levels
			--> Increasing obstruction
			(Greater the value, lesser is the obstruction)
		'''
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			level = self.__map_manager.get_obstruction_level(position)
			self.__r_obstruction[i] = str(level)

	def __set_blockage_levels(self):
		'''
			0,1 : 2 blockage levels
			0: Free
			1: Blocked
		'''
		for i in range(action.Action.num_actions):
			position = self.__action_map[i]
			if self.__map_manager.get_blockage_value(position):
				self.__r_blockage[i] = '1'
			else:
				self.__r_blockage[i] = '0'

	def __set_danger_levels(self):
		'''
			0,1 : 2 danger levels
			0: No danger
			1: Danger
		'''
		seekers = self.__percept.get_seekers()
		for i in range(action.Action.num_actions):
			self.__r_danger[i] = '0'

		for spos in seekers:
			visibility_polygon = self.__map_manager.get_360_visibility_polygon(spos)
			for i in range(action.Action.num_actions):
				if self.__r_danger[i] == '0':
					position = self.__action_map[i]
					if visibility_polygon.is_point_inside(position):
						self.__r_danger[i] = '1'
						

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
			self.__r_hider[i] = '0'
			min_dist = float('inf')
			for hpos in hiders:
				hider_dist = position.get_euclidean_distance(hpos) 
				if hider_dist < min_dist:
					min_dist = hider_dist
			if min_dist >= 0 and min_dist < 5:
				self.__r_hider[i] = '2'
			elif min_dist >= 5 and min_dist < 7:
				self.__r_hider[i] = '1'

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
			self.__r_seeker[i] = '0'
			min_dist = float('inf')
			for spos in seekers:
				seeker_dist = position.get_euclidean_distance(spos) 
				if seeker_dist < min_dist:
					min_dist = seeker_dist
			if min_dist >= 0 and min_dist < 5:
				self.__r_seeker[i] = '2'
			elif min_dist >= 5 and min_dist < 7:
				self.__r_seeker[i] = '1'


class BayesianCuriousController(BayesianController):

	def __init__(self, map_manager, agent_type, sampling=True):
		super(BayesianCuriousController, self).__init__(map_manager, sampling)
		self._considered['target'] = False
		self._considered['obstruction'] = False

class BayesianScaredController(BayesianController):

	def __init__(self, map_manager, agent_type, sampling=True):
		super(BayesianScaredController, self).__init__(map_manager, agent_type, sampling)
		self._considered['target'] = False
		self._considered['visibility'] = False

class BayesianMobileController(BayesianController):

	def __init__(self, map_manager, agent_type, sampling=False):
		super(BayesianMobileController, self).__init__(map_manager, agent_type, sampling)
		self._considered['obstruction'] = False
		self._considered['visibility'] = False

