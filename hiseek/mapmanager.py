import numpy as np

import gamemap

class BasicMapManager(object):
	'''
		Each agent is asoociated with a map manager which helps it to manage
		its map related data.
	'''
	def __init__(self, mapworld):
		self.__mapworld = mapworld

	def get_map(self):
		return self.__mapworld
		



