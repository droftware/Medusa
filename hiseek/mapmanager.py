import math
import os

import numpy as np
import rtree

import gamemap
import coord
import action

class BasicMapManager(object):
	'''
		Each agent is asoociated with a map manager which helps it to manage
		its map related data.
		visibility inference map: Average number of cells visible from a given cell
							      Greater the visbility value, greater the number
							      of cells visible from that cell
		obstruction inference map: Average number of cells from which a given cell 
									visible, Greater the obstruction value, greater 
									the number of cells which can see that cell,
									therfore lesser the obstruction
	'''
	def __init__(self, mapworld, fps, velocity, offset = 10, inference_map=True):
		self.__mapworld = mapworld
		self.__offset = offset
		self.__num_rows = int(math.ceil((mapworld.get_map_width() * 1.0)/offset))
		self.__num_cols = int(math.ceil((mapworld.get_map_height() * 1.0)/offset))
		self.__fps = fps
		self.__dt = 1.0/fps
		self.__velocity = velocity
		self.__visibility = None
		self.__obstruction = None
		self.__visibility_idx = None
		self.__obstruction_penta = [0, 0, 0, 0, 0]
		self.__visibility_penta = [0, 0, 0, 0, 0]
		self.__max_cells_visible = 0

		map_name = mapworld.get_map_name().split('.')[0]
		vis_file = map_name + '.visibility'
		obs_file = map_name + '.obstruction'
		idx_file = map_name + '.index'
		if inference_map:
			if os.path.isfile(vis_file) and os.path.isfile(obs_file) and os.path.isfile(idx_file+'.idx'):
				print('Loading files', vis_file, obs_file, idx_file)
				self.__visibility = np.loadtxt(vis_file)
				self.__obstruction = np.loadtxt(obs_file)
				self.__visibility_idx = rtree.index.Index(idx_file)
			else:
				print('Creating inferences XX')
				self.__visibility = np.zeros((self.__num_rows, self.__num_cols))
				self.__obstruction = np.zeros((self.__num_rows, self.__num_cols))
				# print('Visibility shape:', self.__visibility.shape)
				self.__visibility_idx = rtree.index.Index(idx_file)
				print('Entered map manager')
				id_counter = 0 
				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						position = coord.Coord(i * self.__offset, j * self.__offset)
						if self.__mapworld.check_obstacle_collision(position):
							self.__visibility[i, j] = -1
							self.__obstruction[i, j] = -1
						else:
							x_min = position.get_x()
							y_min = position.get_y() - self.__offset
							x_max = position.get_x() + self.__offset
							y_max = position.get_y()
							bound_box = (x_min, y_min, x_max, y_max)
							# print(bound_box)
							# print(type(self.__visibility_idx))
							self.__visibility_idx.insert(id_counter, bound_box, obj=(i, j))
							id_counter += 1

				# print('Filled all obstacles')
				# print(self.__visibility)

				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						print('Analyzing:',i,j)
						coord_vis = coord.Coord(i * self.__offset, j * self.__offset)
						if self.__visibility[i, j] != -1:
							visibility_polygon = self.get_360_visibility_polygon(coord_vis)
							bbox = self.__mapworld.get_bbox(coord_vis).get_rtree_bbox()
							common_boxes = [box.object for box in self.__visibility_idx.intersection(bbox, objects=True)]
							# print('Common boxes for:',i,j, len(common_boxes))
							for a,b in common_boxes:
								coord_obs = coord.Coord(a * self.__offset, b * self.__offset)
								if visibility_polygon.is_point_inside(coord_obs):
									self.__visibility[i, j] += 1
									self.__obstruction[a, b] += 1

				np.savetxt(map_name.split('.')[0] + '.visibility',self.__visibility)
				np.savetxt(map_name.split('.')[0] + '.obstruction', self.__obstruction)
				self.__visibility_idx.close()

			self.__max_cells_visible = np.amax(self.__visibility)
			print('Max cells visible:', self.__max_cells_visible)

			self.__obstruction_penta[4] = np.amax(self.__obstruction)
			self.__obstruction_penta[0] = np.amin(self.__obstruction)
			self.__obstruction_penta[2] = np.mean(self.__obstruction)
			self.__obstruction_penta[1] = (self.__obstruction_penta[0] + self.__obstruction_penta[2])/2.
			self.__obstruction_penta[3] = (self.__obstruction_penta[2] + self.__obstruction_penta[4])/2.

			self.__visibility_penta[4] = np.amax(self.__visibility)
			self.__visibility_penta[0] = np.amin(self.__visibility)
			self.__visibility_penta[2] = np.mean(self.__visibility)
			self.__visibility_penta[1] = (self.__visibility_penta[0] + self.__visibility_penta[2])/2.
			self.__visibility_penta[3] = (self.__visibility_penta[2] + self.__visibility_penta[4])/2.

	def get_map(self):
		return self.__mapworld

	def get_visibility_polygon(self, current_position, current_rotation, num_rays, visibility_angle):
		return self.__mapworld.get_visibility_polygon(current_position, current_rotation, num_rays, visibility_angle)

	def get_360_visibility_polygon(self, position, num_rays=100):
		return self.get_visibility_polygon(position, 0, num_rays, 180)

	def __get_position_index(self, position):
		row = int(position.get_x())%self.__offset
		col = int(position.get_y())%self.__offset
		return row, col

	def get_visibility_value(self, position):
		row, col = self.__get_position_index(position)
		return self.__visibility[row, col]

	def get_obstruction_value(self, position):
		row, col = self.__get_position_index(position)
		return self.__obstruction[row, col]

	def get_action_map(self, position):
		results = {}
		for move in range(action.Action.num_actions):
			if move != action.Action.ST:
				rotation = action.ROTATION[move]
				rotation_x = math.cos(coord.Coord.to_radians(-rotation))
				rotation_y = math.sin(coord.Coord.to_radians(-rotation))
				vx = self.__velocity * rotation_x
				vy = self.__velocity * rotation_y
				x = position.get_x() + vx * self.__dt
				y = position.get_y() + vy * self.__dt
				results[move] = coord.Coord(x, y)
			else:
				results[move] = position
		return results

	def get_visibility_level(self, position):
		vis_val = self.get_visibility_value(position)
		vis_level = None
		# print()
		# print('visibility penta:', self.__visibility_penta)
		if vis_val == -1:
			vis_level = 0
		elif vis_val >= self.__visibility_penta[0] and vis_val < self.__visibility_penta[1]:
			vis_level = 0
		elif vis_val >= self.__visibility_penta[1] and vis_val < self.__visibility_penta[2]:
			vis_level = 1
		elif vis_val >= self.__visibility_penta[2] and vis_val < self.__visibility_penta[3]:
			vis_level = 2
		elif vis_val >= self.__visibility_penta[3] and vis_val <= self.__visibility_penta[4]:
			vis_level = 3
		# print('Position:', str(position), 'Visibility value:', vis_val, 'Vis level:', vis_level)
		return vis_level


	def get_obstruction_level(self, position):
		obs_val = self.get_obstruction_value(position)
		obs_level = -1
		# print()
		# print('obstruction penta:', self.__obstruction_penta)
		if obs_val == -1:
			obs_level = 0
		elif obs_val >= self.__obstruction_penta[0] and obs_val < self.__obstruction_penta[1]:
			obs_level = 3
		elif obs_val >= self.__obstruction_penta[1] and obs_val < self.__obstruction_penta[2]:
			obs_level = 2
		elif obs_val >= self.__obstruction_penta[2] and obs_val < self.__obstruction_penta[3]:
			obs_level = 1
		elif obs_val >= self.__obstruction_penta[3] and obs_val <= self.__obstruction_penta[4]:
			obs_level = 0
		# print('Position:', str(position), 'Obstruction value:', obs_val, 'Obs level:', obs_level)
		return obs_level

	def get_blockage_value(self, position):
		return self.__mapworld.check_obstacle_collision(position)

	def get_num_rows(self):
		return self.__num_rows

	def get_num_cols(self):
		return self.__num_cols

	def get_max_cells_visible(self):
		return self.__max_cells_visible

	def get_offset(self):
		return self.__offset

class StrategicPointsMapManager(BasicMapManager):

	def __init__(self, mapworld, fps, velocity, offset = 10, inference_map=True):
		'''
			threshold: Strategic points which have a distance less than the 
					   threshold will be merged into one.
		'''
		super(StrategicPointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		all_strtg_pts = []
		self.__strategic_points = []
		self.__threshold = 50

		num_squares = mapworld.get_num_polygons()
		for i in range(num_squares):
			square = mapworld.get_polygon(i)
			mid_edge_points = square.get_mid_edge_points(2)
			for point in mid_edge_points:
				if not mapworld.check_obstacle_collision(point) and not mapworld.check_boundary_collision(point):
					all_strtg_pts.append(point)

		num_all_pts = len(all_strtg_pts)

		deletion_idxs = []
		for i in range(num_all_pts):
			if i in deletion_idxs:
				continue
			for j in range(i+1, num_all_pts):
				if j in deletion_idxs:
					continue
				dist = all_strtg_pts[i].get_euclidean_distance(all_strtg_pts[j])
				if dist < 50:
					# print(i,j, dist)
					deletion_idxs.append(j)

		for i in range(num_all_pts):
			if i not in deletion_idxs:
				self.__strategic_points.append(all_strtg_pts[i])


		self.__num_strategic_points = len(self.__strategic_points)





		# TO DO: Merge strategic points if they are very close to each other and
		# there is no obstacle between them

	def get_num_strategic_points(self):
		return self.__num_strategic_points

	def get_strategic_point(self, i):
		return self.__strategic_points[i]

	def get_strategic_points(self):
		return self.__strategic_points

	def get_closest_strategic_point(self, point):
		min_pt = 0
		min_dist = float("Inf")
		for i in range(self.__num_strategic_points):
			st_pt = self.__strategic_points[i] 
			dist = point.get_euclidean_distance(st_pt)
			if dist < min_dist:
				min_pt = i
				min_dist = dist
		return min_pt

	def get_nearby_visibility_cells(self, current_position):
		bbox = self.__mapworld.get_bbox(current_position).get_rtree_bbox()
		nearby_cells = [box.object for box in self.__visibility_idx.intersection(bbox, objects=True)]
		return nearby_cells




