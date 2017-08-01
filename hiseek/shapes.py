import math

import numpy as np
import matplotlib.path as mplPath
import pyclipper

import coord

class Line(object):

	def __init__(self, a, b):
		assert(isinstance(a, coord.Coord) and isinstance(b, coord.Coord))
		self.__a = a
		self.__b = b

	def __str__(self):
		line_string = str(self.__a) + '---' + str(self.__b)
		return line_string

	def get_a(self):
		return self.__a

	def get_b(self):
		return self.__b

	def __get_diff(self):
		diff_x = self.__a.get_x() - self.__b.get_x()
		diff_y = self.__a.get_y() - self.__b.get_y()
		return diff_x, diff_y


	def get_magnitude(self):
		diff_x, diff_y = self.__get_diff()
		return math.sqrt(diff_x*diff_x + diff_y*diff_y)

	def get_slope(self):
		diff_x, diff_y = self.__get_diff()
		if diff_x != 0:
			slope = (diff_y * 1.0) / diff_x
		else:
			slope = float('Inf')
		return slope

	def get_parametric_form(self):
		'''
			Returns point and direction
		'''
		p_x = self.get_a().get_x()
		p_y = self.get_a().get_y()
		point = coord.Coord(p_x, p_y)
		d_x = self.get_b().get_x() - self.get_a().get_x()
		d_y = self.get_b().get_y() - self.get_a().get_y()
		# assert(d_x != d_y)
		return point, d_x, d_y

	@staticmethod
	def get_intersection(ray, segment):

		r_point, r_dx, r_dy = ray.get_parametric_form()
		r_px = r_point.get_x()
		r_py = r_point.get_y()
		r_mag = ray.get_magnitude()

		s_point, s_dx, s_dy = segment.get_parametric_form()
		s_px = s_point.get_x()
		s_py = s_point.get_y()
		s_mag = segment.get_magnitude()

		if ray.get_slope() == segment.get_slope():
			return None

		t2 = ((r_dx*(s_py-r_py) + r_dy*(r_px-s_px))*1.0)/(s_dx*r_dy - s_dy*r_dx)

		if r_dx != 0:
			t1 = ((s_px+s_dx*t2-r_px)*1.0)/r_dx
		else:
			t1 = ((s_py+s_dy*t2-r_py)*1.0)/r_dy

		if t1 < 0:
			return None
		if t2 < 0 or t2 > 1:
			return None

		i_x = r_px + r_dx*t1
		i_y = r_py + r_dy*t1
		intersect_point = coord.Coord(i_x, i_y)

		# print('Intersect point:')
		# print(intersect_point)
		return intersect_point, t1


class Polygon(object):

	def __init__(self, points_tuple, offset = 1.0 ,line_analysis=False, point_analysis=False):
		assert(len(points_tuple)%2 == 0)
		# print('')
		# print('Points tuple:', points_tuple)
		self.__num_vertices = len(points_tuple)//2
		self.__vertices = []
		self.__line_analysis = line_analysis
		self.__lines = []

		self.__point_analysis = point_analysis
		self.__mpl_path = None
		self.__points_tuple = points_tuple

		if offset == 1.0:
			i = 0
			while i < self.__num_vertices * 2:
				vertex = coord.Coord(points_tuple[i], points_tuple[i+1])
				self.__vertices.append(vertex)
				i += 2
		else:
			i = 0
			offsetted_list = []
			while i < self.__num_vertices * 2:
				vertex = (points_tuple[i], points_tuple[i+1])
				offsetted_list.append(vertex)
				i += 2
			offsetted_tuple = tuple(offsetted_list)	
			pco = pyclipper.PyclipperOffset()
			pco.AddPath(offsetted_tuple, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
			solution = pco.Execute(offset)[0]
			for vertex in solution:
				vcoord = coord.Coord(vertex[0], vertex[1])
				self.__vertices.append(vcoord)

	def __str__(self):
		if not self.__line_analysis:
			self.create_line_representation()
		polygon_string = ''
		for i in range(self.__num_lines):
			polygon_string += str(self.__lines[i]) + ', '
		return polygon_string


	def create_line_representation(self):
		'''
			Creates a list of lines which make the outer boundary of the polygon.
			Helps in finding visibility regions.
		'''
		i = 0
		while i < self.__num_vertices - 1:
			line = Line(self.__vertices[i], self.__vertices[i+1])
			self.__lines.append(line)
			i += 1

		if self.__num_vertices > 2:
			line = Line(self.__vertices[self.__num_vertices - 1], self.__vertices[0])
			self.__lines.append(line)

		self.__num_lines = len(self.__lines)
		self.__line_analysis = True

	def create_path_representation(self):
		'''
			Creates a matplotlib path representation of the polygon.
			Helps in finding fast 'point within the polygon' queries
		'''
		mpl_vertices = []
		for vertex in self.__vertices:
			mpl_vertices.append([vertex.get_x(), vertex.get_y()])

		self.__mpl_path = mplPath.Path(np.array(mpl_vertices))
		self.__point_analysis = True

	def is_point_inside(self, point):
		assert(isinstance(point, coord.Coord))
		if not self.__point_analysis:
			self.create_path_representation()
		return self.__mpl_path.contains_point((point.get_x(), point.get_y()))

	def get_vertex(self, i):
		assert(i < self.__num_vertices)
		return self.__vertices[i]

	def get_vertices(self):
		return self.__vertices

	def get_line(self, i):
		assert(i < self.__num_lines)
		if not self.__line_analysis:
			self.create_line_representation()
		return self.__lines[i]

	def get_points_tuple(self):
		return self.__points_tuple

	def get_num_vertices(self):
		return self.__num_vertices

	def get_num_lines(self):
		if not self.__line_analysis:
			self.create_line_representation()
		return self.__num_lines

class Square(Polygon):

	def __init__(self, centre, length):
		self.__centre = centre
		self.__length = length
		l2 = int(self.__length/2)
		self.__left = centre[0] - l2
		self.__right = centre[0] + l2
		self.__top = centre[1] + l2
		self.__bottom = centre[1] - l2

		
		points_list = [centre[0] - l2, centre[1] - l2, centre[0] - l2, centre[1] + l2, centre[0] + l2, centre[1] + l2, centre[0] + l2, centre[1] - l2]
		points_tuple = tuple(points_list)
		print(points_tuple)
		super(Square, self).__init__(points_tuple)

	def is_point_inside(self, point):
		# assert(isinstance(point, coord.Coord))
		x = point.get_x()
		y = point.get_y()
		if self.__left < x < self.__right and self.__bottom < y < self.__top:
			return True
		else:
			return False 

	def check_aabb_collision(self, other):
		if (self.__centre[0] < other.__centre[0] + other.__length) and (other.__centre[0] < self.__centre[0] + self.__length) and (self.__centre[1] < other.__centre[1] + other.__length) and (other.__centre[1] < self.__centre[1] + self.__length):
			return True
		else:
			return False

	def get_centre(self):
		return self.__centre

	def get_length(self):
		return self.__length





