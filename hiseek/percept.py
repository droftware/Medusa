class Percept(object):
	'''
		Encapsulates the percept aspect of each agent.
	'''
	def __init__(self, hider_coords=[], seeker_coords=[]):
		self.__hider_coords = hider_coords
		self.__seeker_coords = seeker_coords

	def __str__(self):
		percept_string = 'Hiders seen:' + str(self.__hider_coords) + ', Seekers seen:' + str(self.__seeker_coords)
		return percept_string

	def are_hiders_visible(self):
		return bool(self.__hider_coords)

	def are_seekers_visible(self):
		return bool(self.__seeker_coords)

	def get_hiders(self):
		'''
			Returns the positions of visible hiders
		'''
		return self.__hider_coords

	def get_seekers(self):
		'''
			Returns the positions of visible seekers
		'''
		return self.__seeker_coords


class GraphicsPercept(Percept):
	'''
		Percepts used in graphics layer
	'''

	def __init__(self, hider_coords=[], seeker_coords=[], hider_idxs=[], seeker_idxs=[]):
		super(GraphicsPercept, self).__init__(hider_coords, seeker_coords)
		self.__hider_idxs = hider_idxs
		self.__seeker_idxs = seeker_idxs


	def get_hider_idxs(self):
		'''
			Returns the list of hider indices
		'''
		return self.__hider_idxs

	def get_seeker_idxs(self):
		return self.__seeker_idxs


class TeamPercept(Percept):
	'''
		Percepts used in graphics layer
	'''

	def __init__(self, hider_coords=[], seeker_coords=[], hider_uids=[], seeker_uids=[]):
		super(TeamPercept, self).__init__(hider_coords, seeker_coords)
		self.__hider_uids = hider_uids
		self.__seeker_uids = seeker_uids

	def get_hider_uids(self):
		'''
			Returns the list of tuples (Rank, id)
		'''
		return self.__hider_uids

	def get_seeker_uids(self):
		return self.__seeker_uids





