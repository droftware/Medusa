import os

import shapes

class PolygonMap(object):
	'''
		Represents a map in the form of a list of polygons.
	'''


	def __init__(self, map_id):
		self.__polygons = []
		self.__boundary_polygon = None

		map_name = 'id_' + str(map_id) + '.polygons'
		# print('Path:', map_name)
		assert(os.path.isfile(map_name))
		f = open(map_name, 'r')
		first = True
		for line in f:
			line.strip()
			points_list = line.split(',')
			if len(line) != 0:
				if first:
					self.__width = int(points_list[0])
					self.__height = int(points_list[1])

					points_tuple = (0, 0, self.__width, 0, self.__width, self.__height, 0, self.__height)
					self.__boundary_polygon = shapes.Polygon(points_tuple)
					first = False
				else:
					points_list = [int(point) for point in points_list]
					points_tuple = tuple(points_list)
					polygon = shapes.Polygon(points_tuple)
					self.__polygons.append(polygon)

		self.__num_polygons = len(self.__polygons)


	def get_num_polygons(self):
		return self.__num_polygons

	def get_map_width(self):
		return self.__width

	def get_map_height(self):
		return self.__height

	def get_polygon(self, i):
		assert(i < self.__num_polygons)
		return self.__polygons[i]

	def get_boundary_polygon(self):
		return self.__boundary_polygon



