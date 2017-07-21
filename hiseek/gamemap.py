import os
import math

import shapes
import coord

class PolygonMap(object):
	'''
		Represents a map in the form of a list of polygons.
	'''


	def __init__(self, map_id):
		self.__polygons = []
		self.__boundary_polygon = None
		self.__all_polygons = None # Includes all the obstacle polygons as well as boundary polygon

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
		self.__all_polygons = self.__polygons + [self.__boundary_polygon]


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

	def check_obstacle_collision(self, position):
		'''
			Returns True if point collides(is inside) any
			obstacle polygon.
		'''
		for i in range(self.__num_polygons):
			polygon = self.__polygons[i]
			if polygon.is_point_inside(position):
				return True
		return False

	def to_radians(degrees):
		return math.pi * degrees / 180.0

	def get_visibility_polygon(self, current_position, current_rotation, num_rays, visibility_angle):
		# c = coord.Coord(self.x, self.y)
		vis_points = [int(current_position.get_x()), int(current_position.get_y())]

		rotation = current_rotation - visibility_angle
		offset = (visibility_angle * 2.0)/num_rays
		while rotation < current_rotation + visibility_angle:
			rotation_x = math.cos(PolygonMap.to_radians(-rotation))
			rotation_y = math.sin(PolygonMap.to_radians(-rotation))
			r = coord.Coord(current_position.get_x() + rotation_x, current_position.get_y() + rotation_y)
			ray = shapes.Line(current_position, r)
			# print('ray:', ray)
			closest_intersect = None
			for polygon in self.__all_polygons:
				# print('polygon:',polygon)
				for i in range(polygon.get_num_lines()):
					
					intersect = shapes.Line.get_intersection(ray, polygon.get_line(i))
					if not intersect:
						continue
					if not closest_intersect or intersect[1] < closest_intersect[1]:
						closest_intersect = intersect

			# print(closest_intersect[0])
			
			assert(closest_intersect)
			vis_points.append(int(closest_intersect[0].get_x()))
			vis_points.append(int(closest_intersect[0].get_y()))

			rotation += offset

		vis_points_tuple = tuple(vis_points)
		visibility_polygon = shapes.Polygon(vis_points_tuple)
		return visibility_polygon



