import os

import shapes

class PolygonMap(object):
	'''
		Represents a map in the form of a list of polygons.
	'''


	def __init__(self, map_id):
		self.__polygons = []

		map_name = 'id_' + str(map_id) + '.polygons'
		print('Path:', map_name)
		assert(os.path.isfile(map_name))
		f = open(map_name, 'r')
		for line in f:
			line.strip()
			if len(line) != 0:
				points_list = line.split(',')
				points_list = [int(point) for point in points_list]
				points_tuple = tuple(points_list)
				polygon = shapes.Polygon(points_tuple)
				self.__polygons.append(polygon)

		self.__num_polygons = len(self.__polygons)

	def get_num_polygons(self):
		return self.__num_polygons

	def get_polygon(self, i):
		assert(i < self.__num_polygons)
		return self.__polygons[i]

