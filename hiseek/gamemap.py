import os
import math

import rtree

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
		self.__map_name = 'id_' + str(map_id) + '.polygons'
		print('Map name:', self.__map_name)

		self.__expansion_factor = 2.50
		self.__expanded_polygons = []

		self.__bbox_length = 250

		self.__rtree_idx = rtree.index.Index()

		print('Path:', self.__map_name)
		assert(os.path.isfile(self.__map_name))
		f = open(self.__map_name, 'r')
		first = True
		for line in f:
			line.strip()
			if len(line) != 0:
				if first:
					points_list = line.split(',')
					self.__width = int(points_list[0])
					self.__height = int(points_list[1])

					points_tuple = (0, 0, self.__width, 0, self.__width, self.__height, 0, self.__height)
					self.__boundary_polygon = shapes.Polygon(points_tuple)

					offset = 10
					points_tuple = (offset, offset, self.__width - offset, offset, self.__width - offset, self.__height - offset, offset, self.__height-offset)
					self.__imaginary_boundary = shapes.Polygon(points_tuple)
					first = False
				else:
					geometry_type = line.split(':')[0].strip()
					# print(geometry_type)
					points_string = line.split(':')[1]
					points_list = points_string.split(',')
					# print(points_list)
					points_list = [int(point) for point in points_list]
					points_tuple = tuple(points_list)
					polygon = None
					if geometry_type == 'polygon':
						polygon = shapes.Polygon(points_tuple)
						# print(' ')
						# print(polygon)
						
						# print('Expanded polygon:')
						e_polygon = shapes.Polygon(points_tuple, self.__expansion_factor)
						# print(e_polygon)
						self.__expanded_polygons.append(e_polygon)
					if geometry_type == 'square':
						centre = (points_tuple[0], points_tuple[1])
						length = points_tuple[2]
						# print(centre)
						# print(length)
						polygon = shapes.Square(centre, length)
					self.__rtree_idx.insert(len(self.__polygons), polygon.get_rtree_bbox(), obj=polygon)
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

	def get_bbox(self, current_position):
		bbox = shapes.Square((current_position.get_x(), current_position.get_y()), self.__bbox_length)
		return bbox

	def get_map_name(self):
		return self.__map_name

	def check_boundary_collision(self, position):
		'''
			Returns True if point collides with the boundary
		'''
		if self.__boundary_polygon.is_point_inside(position):
			return False
		return True

	def check_obstacle_collision(self, position, expanded=False):
		'''
			Returns True if point collides(is inside) any
			obstacle polygon.
		'''
		if expanded:
			polygons = self.__expanded_polygons
		else:
			polygons = self.__polygons
		for i in range(self.__num_polygons):
			polygon = polygons[i]
			if polygon.is_point_inside(position):
				return True
		return False


	def get_visibility_polygon(self, current_position, current_rotation, num_rays, visibility_angle):
		# c = coord.Coord(self.x, self.y)
		vis_points = [int(current_position.get_x()), int(current_position.get_y())]

		rotation = current_rotation - visibility_angle
		offset = (visibility_angle * 2.0)/num_rays

		bbox = self.get_bbox(current_position)
		hits = list(self.__rtree_idx.intersection(bbox.get_rtree_bbox(), objects=True))
		polygon_hits = [item.object for item in hits]

		# polygon_ids = [item.id for item in hits]
		# print('Polygons considered:', polygon_ids)
		nearby_polygons = polygon_hits + [bbox] + [self.__boundary_polygon]
		while rotation < current_rotation + visibility_angle:
			rotation_x = math.cos(coord.Coord.to_radians(-rotation))
			rotation_y = math.sin(coord.Coord.to_radians(-rotation))
			r = coord.Coord(current_position.get_x() + rotation_x, current_position.get_y() + rotation_y)
			rotation += offset
			if r.get_x() < 0 or r.get_x() > self.__width or r.get_y() < 0 or r.get_y() > self.__height:
				vis_points.append(int(current_position.get_x()))
				vis_points.append(int(current_position.get_y()))
				continue
			ray = shapes.Line(current_position, r)
			# print('ray:', ray)
			closest_intersect = None
			for polygon in nearby_polygons:
				# print('polygon:',polygon)
				for i in range(polygon.get_num_lines()):
					
					intersect = shapes.Line.get_intersection(ray, polygon.get_line(i))
					if not intersect:
						continue
					if not closest_intersect or intersect[1] < closest_intersect[1]:
						closest_intersect = intersect

			

			if not closest_intersect:
				print('Closest intersect not found')
				print('From coordinate:', current_position)
				print('Ray:', ray)
				print('Segment:', polygon.get_line(i))
				continue

			vis_points.append(int(closest_intersect[0].get_x()))
			vis_points.append(int(closest_intersect[0].get_y()))

			

		vis_points_tuple = tuple(vis_points)
		visibility_polygon = shapes.Polygon(vis_points_tuple)
		return visibility_polygon
