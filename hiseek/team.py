from abc import ABCMeta, abstractmethod
import copy

import message
import agent
import mapmanager
import coord
import ucb

class Team(object):
	'''
		An abstract base class describing the Team framework which controls and
		manages the individual agents of a particular team of hiders/seekers.
	'''

	__metaclass__ = ABCMeta

	ranks = 0 
	# ranks denote the hierarchy of the team, rank 1 means a flat hierarchy team,
	# rank 2 means there are higher level players who control lower level players 
	# and so on

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta):
		'''
			_members is a list of lists, each list contains members
			of the particular rank which corresponds to the index at which
			this list is stored.
		'''
		self.__agent_type = agent_type
		self._num_agents = num_agents
		self._mapworld = mapworld
		self._fps = fps
		self._time_quanta = 1.0/fps
		self._velocity = velocity
		self._fixed_time_quanta = fixed_time_quanta
		self._distance_quanta = self._time_quanta * self._velocity
		self._team_messenger = message.TeamMessenger()
		self._members = None # which type of members to recruit ?
		self._map_managers = None # which map manager to assign to each hierarchy level ?
		self._active = None # a list denoting which of the agents are still in the game
	
	def create_agent_messenger(self, agent_id):
		return self._team_messenger.create_agent_messenger(agent_id)

	def get_num_agents(self):
		'''
			Returns the total number of agents present in the team.
		'''
		return self._num_agents


	def get_ranks(self):
		return self.ranks

	def get_distance_quanta(self):
		return self._distance_quanta

	def get_num_rankers(self, rank):
		'''
			Returns number of units having a particular rank
		'''
		assert(rank < self.ranks)
		return len(self._members[rank])

	def set_percept(self, rank, idx, current_percept):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		member = self._members[rank][idx]
		member.set_percept(current_percept)

	def get_percept(self, rank, idx):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		member = self._members[rank][idx]
		return member.get_percept()

	def get_action(self, rank, idx):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		member = self._members[rank][idx]
		return member.get_action()

	def set_position(self, rank, idx, position):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		self._members[rank][idx].set_position(position)

	def get_position(self, rank, idx):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		return self._members[rank][idx].get_position()

	def set_member_inactive(self, rank, idx):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		assert(self._active[rank][idx])
		self._active[rank][idx] = False

	def is_member_active(self, rank, idx):
		assert(rank < self.ranks)
		assert(idx < len(self._members[rank]))
		return self._active[rank][idx]

	def __enable_message_generation(self):
		''' 
		Based on the percept obtained, generate messages and pass them
		according to the team hierarchy, starting from the highest ranking
		agents to the lowest ranking agents
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				if self._active[i][j]:
					member = self._members[i][j]
					member.generate_messages()

	def __enable_message_analysis(self):
		'''
		The messages are analyzed, starting from high ranking agents to lower
		level agents. Based on this analysis some temporary state may be 
		changed affecting the chosen action
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				if self._active[i][j]:
					member = self._members[i][j]
					member.analyze_messages()

	def __enable_action_selection(self):
		'''
		Based on the percept as well as temporary state changes(due to prior)
		message analysis, action is chosen
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				if self._active[i][j]:
					member = self._members[i][j]
					member.select_action()

	def __enable_temporal_state_clearance(self):
		'''
		Clear any temporary state changes caused by message analysis
		to their normal values
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				if self._active[i][j]:
					member = self._members[i][j]
					member.clear_temporary_state()


	def select_actions(self):
		'''
			Assigns actions to each of its members.

			Based on the current percept, as well as the message passed 
			b/w the members, each agent takes an action
		'''
		
		# self.__enable_message_generation()
		# self.__enable_message_analysis()
		self.__enable_action_selection()
		self.__enable_temporal_state_clearance()


class RandomTeam(Team):

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta):
		super(RandomTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]

		# assign a basic map manager to the only level
		map_manager = mapmanager.BasicMapManager(self._mapworld, self._fps, self._velocity)
		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		agent_id = 'RH' + str(0)
		commander_member = agent.RandomCommanderAgent(agent_type, agent_id, self, self._map_managers[0])
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			member = agent.RandomAgent(agent_type, agent_id, self, self._map_managers[0])
			self._members[0].append(member)
			self._active[0].append(True)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)


class BayesianTeam(Team):

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta):
		super(BayesianTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]

		# assign a basic map manager to the only level
		map_manager = mapmanager.BasicMapManager(self._mapworld, self._fps, self._velocity)
		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		agent_id = 'RH' + str(0)
		commander_member = agent.BayesianCommanderAgent(agent_type, agent_id, self, self._map_managers[0])
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			member = agent.BayesianAgent(agent_type, agent_id, self, self._map_managers[0])
			self._members[0].append(member)
			self._active[0].append(True)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)


class UCBAggressiveTeam(Team):

	# TO DO: Extend it for multiple agents

	ranks = 1

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta, num_rays, visibility_angle):
		super(UCBAggressiveTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[]]
		self._active = [[]]

		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		# assign a basic map manager to the only level
		map_manager = mapmanager.StrategicPointsMapManager(self._mapworld, self._fps, self._velocity)

		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		agent_id = 'RH' + str(0)
		commander_member = agent.UCBAggressiveCommanderAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
		self._members[0].append(commander_member)
		self._active[0].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			member = agent.UCBAggressiveAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
			self._members[0].append(member)
			self._active[0].append(True)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)

		# # Set the opening position of the lone agent
		# position = commander_member.get_opening_position(0, 0)
		# self._members[0][0].set_position(position)



class UCBPassiveTeam(Team):

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta, num_rays, visibility_angle, handicap_movement=False, handicap_visibility=False):		
		super(UCBPassiveTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]
		self.__handicap_movement = handicap_movement
		self.__handicap_visibility = handicap_visibility

		if self.__handicap_movement:
			print('Hider is movement Handicapped')
		else:
			print('Hider is NOT movement Handicapped')

		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		map_manager = mapmanager.StrategicPointsMapManager(self._mapworld, self._fps, self._velocity)
		self._map_managers.append(map_manager)
		num_strategic_points = self._map_managers[0].get_num_strategic_points()
		macro_UCB = ucb.UCB(num_strategic_points)
		offset = self._map_managers[0].get_offset()
		max_cells_visible = self._map_managers[0].get_max_cells_visible()

		for i in range(num_strategic_points):
			avg_val = 0
			if not self.__handicap_visibility:
				strategic_point = self._map_managers[0].get_strategic_point(i)
				vpolygon = self._map_managers[0].get_360_visibility_polygon(strategic_point, self.__num_rays)
				common_cells = self._map_managers[0].get_nearby_visibility_cells(strategic_point)
				visible_cells = 0
				for a, b in common_cells:
					coord_obs = coord.Coord(a * offset, b * offset)
					if vpolygon.is_point_inside(coord_obs):
						visible_cells += 1
				if visible_cells == 0:
					visible_cells = 1
				avg_val = max_cells_visible * 1.0/ visible_cells
			# print('Setting avg value:', avg_val)
			macro_UCB.set_initial_average(i, avg_val)

		macro_UCB.set_initial_bounds()
		print('Hider macro UCB:', str(macro_UCB))

		# recruit the commander of the random team
		agent_id = 'RH' + str(0)
		cm_ucb = copy.deepcopy(macro_UCB)
		commander_member = agent.UCBPassiveCommanderAgent(agent_type, agent_id, self, self._map_managers[0], cm_ucb, self.__num_rays, self.__visibility_angle, self.__handicap_movement)
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			m_ucb = copy.deepcopy(macro_UCB)
			member = agent.UCBPassiveAgent(agent_type, agent_id, self, self._map_managers[0], m_ucb, self.__num_rays, self.__visibility_angle, self.__handicap_movement)
			self._members[0].append(member)
			self._active[0].append(True)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)

class UCBCoverageTeam(Team):

	# TO DO: Extend it for multiple agents

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta, num_rays, visibility_angle):
		super(UCBCoverageTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]
		

		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		# assign a basic map manager to the only level
		# map_manager = mapmanager.StrategicPointsMapManager(self._mapworld, self._fps, self._velocity)
		map_manager = mapmanager.CoveragePointsMapManager(self._mapworld, self._fps, self._velocity, self.__num_rays, self.__visibility_angle)

		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		# agent_id = 'RH' + str(0)
		agent_id = 0
		commander_member = agent.UCBCoverageCommanderAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			agent_id = i+1
			member = agent.UCBCoverageAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
			self._members[0].append(member)
			self._active[0].append(True)

		print('Members:', self._members)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)


class UCBCoverageCommunicationTeam(Team):

	# TO DO: Extend it for multiple agents

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta, num_rays, visibility_angle):
		super(UCBCoverageCommunicationTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]
		
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle

		# assign a basic map manager to the only level
		map_manager = mapmanager.CoveragePointsMapManager(self._mapworld, self._fps, self._velocity, self.__num_rays, self.__visibility_angle)

		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		# agent_id = 'RH' + str(0)
		agent_id = 0
		commander_member = agent.UCBCoverageCommunicationCommanderAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = i+1
			member = agent.UCBCoverageCommunicationAgent(agent_type, agent_id, self, self._map_managers[0], self.__num_rays, self.__visibility_angle)
			self._members[0].append(member)
			self._active[0].append(True)

		# print('Members:', self._members)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)

		# Get opening coverage points for the agents
		agent_id = 0
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				coverage_point = commander_member.get_opening_coverage_point(agent_id)
				self._members[i][j].set_initial_coverage_point(coverage_point)
				agent_id += 1


class HumanRandomTeam(Team):

	ranks = 2

	def __init__(self, agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta):
		super(HumanRandomTeam, self).__init__(agent_type, num_agents, mapworld, fps, velocity, fixed_time_quanta)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[], []]
		self._active = [[], []]
		self._human_id = (1, 0)

		# assign a basic map manager to the only level
		map_manager = mapmanager.BasicMapManager(self._mapworld, self._fps, self._velocity)
		self._map_managers.append(map_manager)

		# recruit the commander of the random team
		agent_id = 'RH' + str(0)
		commander_member = agent.HumanRandomCommanderAgent(agent_type, agent_id, self, self._map_managers[0], True)
		self._members[1].append(commander_member)
		self._active[1].append(True)

		# recruit agents for the team
		for i in range(self._num_agents - 1):
			agent_id = 'RH' + str(i)
			member = agent.HumanRandomAgent(agent_type, agent_id, self, self._map_managers[0], False)
			self._members[0].append(member)
			self._active[0].append(True)

		# Get the opening positions from the commader member and set each agents
		# position accordingly
		for i in reversed(range(self.ranks)):
			for j in range(self.get_num_rankers(i)):
				position = commander_member.get_opening_position(i, j)
				self._members[i][j].set_position(position)

	def set_key(self, key):
			self._members[self._human_id[0]][self._human_id[1]].set_key(key)
			# print('Key Set:', self._key)

	def get_human_agent_id(self):
		return self._human_id

	def toggle_human_player(self):
		total_ranks = len(self._members)
		self._members[self._human_id[0]][self._human_id[1]].set_is_human_param(False)

		if self._human_id[1] == len(self._members[self._human_id[0]]) - 1:
			self._human_id = ((self._human_id[0] + 1) % total_ranks, 0)
		else:
			self._human_id = (self._human_id[0], self._human_id[1] + 1)
		self._members[self._human_id[0]][self._human_id[1]].set_is_human_param(True)