import numpy as np
import math

class Vector2D(object):
	def __init__(self, x, y):
		self.__x = x
		self.__y = y

		self.__magnitude = math.sqrt(self.__x * self.__x + self.__y * self.__y)

	def __str__(self):
		vector_string = str(self.__x)+':x , ' + str(self.__y) +':y'
		return vector_string

	@classmethod
	def from_coordinates(cls, coord_A, coord_B):
		'''
			Gets a vector of form 'coord_A - coord_B'
		'''
		x = coord_A.get_x() - coord_B.get_x()
		y = coord_A.get_y() - coord_B.get_y()
		return cls(x, y)

	def get_magnitude(self):
		return self.__magnitude

	def normalize(self):
		'''
			Makes the length of the vector to 1
		'''
		mag = self.get_magnitude()
		assert(mag != 0)
		self.__x = self.__x * 1.0 / mag
		self.__y = self.__y * 1.0 / mag
		self.__magnitude = 1.0


	def dot_product(self, other):
		dot_product = self.__x * other.__x + self.__y * other.__y
		return dot_product
