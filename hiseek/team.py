from abc import ABCMeta, abstractmethod

import message
import agent
import mapmanager

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

	def __init__(self, num_agents):
		'''
			_members is a list of lists, each list contains members
			of the particular rank which corresponds to the index at which
			this list is stored.
		'''
		self._num_agents = num_agents
		self._team_messenger = message.TeamMessageManager()
		self._members = None # which type of members to recruit ?
		self._map_managers = None # which map manager to assign to each hierarchy level ?

	def create_agent_messenger(self, agent_id):
		return self._team_messenger.create_agent_messenger(agent_id)

	def get_ranks(self):
		return self.ranks
			
	def get_members(self, rank):
		'''
			Get all the members of a specfic rank
		'''
		assert(rank < self.ranks)
		return self._members[rank]

	def __enable_message_generation(self):
		''' 
		Based on the percept obtained, generate messages and pass them
		according to the team hierarchy, starting from the highest ranking
		agents to the lowest ranking agents
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
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
				member = self._members[i][j]
				member.analyze_messages()

	def __enable_action_selection(self):
		'''
		Based on the percept as well as temporary state changes(due to prior)
		message analysis, action is chosen
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				member = self._members[i][j]
				member.select_action()

	def __enable_temporal_state_clearance(self):
		'''
		Clear any temporary state changes caused by message analysis
		to their normal values
		'''
		for i in reversed(range(0, self.ranks)):
			for j in range(len(self._members[i])):
				member = self._members[i][j]
				member.clear_temporary_state()


	def select_actions(self):
		'''
			Assigns actions to each of its members.

			Based on the current percept, as well as the message passed 
			b/w the members, each agent takes an action
		'''
		
		self.__enable_message_generation()
		self.__enable_message_analysis()
		self.__enable_action_selection()
		self.__enable_temporal_state_clearance()
		

	@abstractmethod
	def team_type(self):
		pass

class HiderTeam(Team):

	__metaclass__ = ABCMeta

	def team_type(self):
		return 'hider_team'

class SeekerTeam(Team):

	__metaclass__ = ABCMeta

	def team_type(self):
		return 'seeker_team'

class RandomHiderTeam(HiderTeam):

	ranks = 1

	def __init__(self, num_agents, mapworld):
		super(RandomHiderTeam, self).__init__(num_agents)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[]]

		# assign a basic map manager to the only level
		map_manager = mapmanager.BasicMapManager(mapworld)
		self._map_managers.append(map_manager)

		# recruit agents for the team
		for i in range(self._num_agents):
			agent_id = 'RH' + str(i)
			member = agent.RandomSeekerAgent(agent_id, self, self._map_managers[0])
			self._members[0].append(member)

class RandomSeekerTeam(SeekerTeam):

	ranks = 1

	def __init__(self, num_agents, mapworld):
		super(RandomSeekerTeam, self).__init__(num_agents)

		# prepare a rank 1 hierarchy member list and map managers
		self._map_managers = [] # one map manager for one level
		self._members = [[]]

		# assign a basic map manager to the only level
		map_manager = mapmanager.BasicMapManager(mapworld)
		self._map_managers.append(map_manager)

		# recruit agents for the team
		for i in range(self._num_agents):
			agent_id = 'RS' + str(i)
			member = agent.RandomSeekerAgent(agent_id, self, self._map_managers[0])
			self._members[0].append(member)
