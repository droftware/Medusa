class Percept(object):
	'''
		Encapsulates the percept aspect of each agent.
	'''
	def __init__(self):
		self.__hiders = []
		self.__seekers = []

	def are_hiders_visible(self):
		return bool(self.__hiders)

	def are_seekers_visible(self):
		return bool(self.__seekers)

	def get_hiders(self):
		'''
			Returns the positions of visible hiders
		'''
		return self.__hiders

	def get_seekers(self):
		'''
			Returns the positions of visible seekers
		'''
		return self.__seekers


