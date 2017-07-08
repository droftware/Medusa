
class Statistic(object):
	"""
		Stores various kind of in-game statistics for one complete simulation.
	"""

	def __init__(self, num_hiders, num_seekers):
		self.__total_time = 0
		self.__catch_time = [0 for i in range(num_hiders)]
		self.__avg_seeker_visibility = 0
		self.__avg_hider_visibility = 0
