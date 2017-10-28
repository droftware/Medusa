import math
import os

import numpy as np
import rtree
import networkx as nx

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
		self._mapworld = mapworld
		self.__offset = offset
		self.__num_rows = int(math.ceil((mapworld.get_map_width() * 1.0)/offset))
		self.__num_cols = int(math.ceil((mapworld.get_map_height() * 1.0)/offset))
		self.__fps = fps
		self.__dt = 1.0/fps
		self.__velocity = velocity
		self._visibility = None
		self._obstruction = None
		self._visibility_idx = None
		self._obstruction_penta = [0, 0, 0, 0, 0]
		self._visibility_penta = [0, 0, 0, 0, 0]
		self.__max_cells_visible = 0

		map_name = mapworld.get_map_name().split('.')[0]
		vis_file = map_name + '.visibility'
		obs_file = map_name + '.obstruction'
		idx_file = map_name + '.index'
		if inference_map:
			if os.path.isfile(vis_file) and os.path.isfile(obs_file) and os.path.isfile(idx_file+'.idx'):
				print('Loading files', vis_file, obs_file, idx_file)
				self._visibility = np.loadtxt(vis_file)
				self._obstruction = np.loadtxt(obs_file)
				self._visibility_idx = rtree.index.Index(idx_file)
			else:
				print('Creating inferences XX')
				self._visibility = np.zeros((self.__num_rows, self.__num_cols))
				self._obstruction = np.zeros((self.__num_rows, self.__num_cols))
				# print('Visibility shape:', self._visibility.shape)
				self._visibility_idx = rtree.index.Index(idx_file)
				print('Entered map manager')
				id_counter = 0 
				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						position = coord.Coord(i * self.__offset, j * self.__offset)
						if self._mapworld.check_obstacle_collision(position):
							self._visibility[i, j] = -1
							self._obstruction[i, j] = -1
						else:
							x_min = position.get_x()
							y_min = position.get_y() - self.__offset
							x_max = position.get_x() + self.__offset
							y_max = position.get_y()
							bound_box = (x_min, y_min, x_max, y_max)
							# print(bound_box)
							# print(type(self._visibility_idx))
							self._visibility_idx.insert(id_counter, bound_box, obj=(i, j))
							id_counter += 1

				# print('Filled all obstacles')
				# print(self._visibility)

				for i in range(self.__num_rows):
					for j in range(self.__num_cols):
						print('Analyzing:',i,j)
						coord_vis = coord.Coord(i * self.__offset, j * self.__offset)
						if self._visibility[i, j] != -1:
							visibility_polygon = self.get_360_visibility_polygon(coord_vis)
							bbox = self._mapworld.get_bbox(coord_vis).get_rtree_bbox()
							common_boxes = [box.object for box in self._visibility_idx.intersection(bbox, objects=True)]
							# print('Common boxes for:',i,j, len(common_boxes))
							for a,b in common_boxes:
								coord_obs = coord.Coord(a * self.__offset, b * self.__offset)
								if visibility_polygon.is_point_inside(coord_obs):
									self._visibility[i, j] += 1
									self._obstruction[a, b] += 1

				np.savetxt(map_name.split('.')[0] + '.visibility',self._visibility)
				np.savetxt(map_name.split('.')[0] + '.obstruction', self._obstruction)
				self._visibility_idx.close()

			self.__max_cells_visible = np.amax(self._visibility)
			print('Max cells visible:', self.__max_cells_visible)

			self._obstruction_penta[4] = np.amax(self._obstruction)
			self._obstruction_penta[0] = np.amin(self._obstruction)
			self._obstruction_penta[2] = np.mean(self._obstruction)
			self._obstruction_penta[1] = (self._obstruction_penta[0] + self._obstruction_penta[2])/2.
			self._obstruction_penta[3] = (self._obstruction_penta[2] + self._obstruction_penta[4])/2.

			self._visibility_penta[4] = np.amax(self._visibility)
			self._visibility_penta[0] = np.amin(self._visibility)
			self._visibility_penta[2] = np.mean(self._visibility)
			self._visibility_penta[1] = (self._visibility_penta[0] + self._visibility_penta[2])/2.
			self._visibility_penta[3] = (self._visibility_penta[2] + self._visibility_penta[4])/2.

	def get_map(self):
		return self._mapworld

	def get_visibility_polygon(self, current_position, current_rotation, num_rays, visibility_angle):
		return self._mapworld.get_visibility_polygon(current_position, current_rotation, num_rays, visibility_angle)

	def get_360_visibility_polygon(self, position, num_rays=10):
		return self.get_visibility_polygon(position, 0, num_rays, 180)

	def __get_position_index(self, position):
		row = int(position.get_x())%self.__offset
		col = int(position.get_y())%self.__offset
		return row, col

	def get_visibility_value(self, position):
		row, col = self.__get_position_index(position)
		return self._visibility[row, col]

	def get_obstruction_value(self, position):
		row, col = self.__get_position_index(position)
		return self._obstruction[row, col]

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
		# print('visibility penta:', self._visibility_penta)
		if vis_val == -1:
			vis_level = 0
		elif vis_val >= self._visibility_penta[0] and vis_val < self._visibility_penta[1]:
			vis_level = 0
		elif vis_val >= self._visibility_penta[1] and vis_val < self._visibility_penta[2]:
			vis_level = 1
		elif vis_val >= self._visibility_penta[2] and vis_val < self._visibility_penta[3]:
			vis_level = 2
		elif vis_val >= self._visibility_penta[3] and vis_val <= self._visibility_penta[4]:
			vis_level = 3
		# print('Position:', str(position), 'Visibility value:', vis_val, 'Vis level:', vis_level)
		return vis_level


	def get_obstruction_level(self, position):
		obs_val = self.get_obstruction_value(position)
		obs_level = -1
		# print()
		# print('obstruction penta:', self._obstruction_penta)
		if obs_val == -1:
			obs_level = 0
		elif obs_val >= self._obstruction_penta[0] and obs_val < self._obstruction_penta[1]:
			obs_level = 3
		elif obs_val >= self._obstruction_penta[1] and obs_val < self._obstruction_penta[2]:
			obs_level = 2
		elif obs_val >= self._obstruction_penta[2] and obs_val < self._obstruction_penta[3]:
			obs_level = 1
		elif obs_val >= self._obstruction_penta[3] and obs_val <= self._obstruction_penta[4]:
			obs_level = 0
		# print('Position:', str(position), 'Obstruction value:', obs_val, 'Obs level:', obs_level)
		return obs_level

	def get_blockage_value(self, position):
		return self._mapworld.check_obstacle_collision(position)

	def get_num_rows(self):
		return self.__num_rows

	def get_num_cols(self):
		return self.__num_cols

	def get_max_cells_visible(self):
		return self.__max_cells_visible

	def get_offset(self):
		return self.__offset

	def get_cell_from_coord(self, postn):
		row = int(postn.get_x()/self.__offset)
		col = int(postn.get_y()/self.__offset)
		return (row, col)

	def get_coord_from_cell(self, row, col):
		'''
			Retruns the cell corresponding to the cell
			The coordinate returned is the mid point of the cell
		'''
		x = int(row * self.__offset - self.__offset/2)
		y = int(col * self.__offset - self.__offset/2)
		cell_coord = coord.Coord(x, y)
		return cell_coord


class StrategicPointsMapManager(BasicMapManager):

	def __init__(self, mapworld, fps, velocity, offset = 10, inference_map=True):
		'''
			threshold: Strategic points which have a distance less than the 
					   threshold will be merged into one.
		'''
		super(StrategicPointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		all_strtg_pts = []
		self._strategic_points = []
		self.__threshold = 50
		self.__strategic_pts_idx = rtree.index.Index()

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

		j = 0
		for i in range(num_all_pts):
			if i not in deletion_idxs:
				# print(j,'St pt', str(all_strtg_pts[i]))
				st_pt = StrategicPoint(all_strtg_pts[i].get_x(), all_strtg_pts[i].get_y(), j)
				# self._strategic_points.append(all_strtg_pts[i])
				self._strategic_points.append(st_pt)	
				cx = all_strtg_pts[i].get_x()
				cy = all_strtg_pts[i].get_y()
				bound_box = (cx, cy, cx, cy)
				self.__strategic_pts_idx.insert(j, bound_box, obj=j)
				j += 1


		self._num_strategic_points = len(self._strategic_points)
		# print('Number of strategic points:', self._num_strategic_points)

		# TO DO: Merge strategic points if they are very close to each other and
		# there is no obstacle between them

	def get_num_strategic_points(self):
		return self._num_strategic_points

	def get_strategic_point(self, i):
		return self._strategic_points[i]

	def get_strategic_points(self):
		return self._strategic_points

	def get_closest_strategic_point(self, point, num_points = 1):
		cx = point.get_x()
		cy = point.get_y()
		bound_box = (cx, cy, cx, cy)
		closest_st_pts = list(self.__strategic_pts_idx.nearest(bound_box, num_points))
		# print('Closest points:', closest_st_pts)
		if len(closest_st_pts) != num_points:
			closest_st_pts = list(np.random.choice(closest_st_pts, num_points, replace=False))
		return closest_st_pts

		# for i in range(self._num_strategic_points):
		# 	st_pt = self._strategic_points[i] 
		# 	dist = point.get_euclidean_distance(st_pt)
		# 	if dist < min_dist:
		# 		min_pt = i
		# 		min_dist = dist
		# return min_pt

	def get_nearby_visibility_cells(self, current_position):
		bbox = self._mapworld.get_bbox(current_position).get_rtree_bbox()
		nearby_cells = [box.object for box in self._visibility_idx.intersection(bbox, objects=True)]
		return nearby_cells


class StrategicPoint(coord.Coord):
	def __init__(self, x, y, unique_id):
		super(StrategicPoint, self).__init__(x, y)
		self.__id = unique_id
		self._covered = False
		self.__visible_cells_set = None
		self.__common_strategic_points = []
		self.__num_cells_common = []

	def mark_covered(self):
		self._covered = True

	def is_covered(self):
		return self._covered

	def set_visible_cells_set(self, visible_cells_set):
		self.__visible_cells_set = visible_cells_set

	def get_visible_cells_set(self):
		return self.__visible_cells_set

	def set_common_strategic_point(self, stpoint_idx, num_cells):
		self.__common_strategic_points.append(stpoint_idx)
		self.__num_cells_common.append(num_cells)

	def __str__(self):
		point_string = '('+ str(self.get_x()) + ':' + str(self.get_y()) + '); ' + 'Common strategic points:' + str(self.__common_strategic_points) +' Number common cells:' + str(self.__num_cells_common) 
		return point_string

class CoveragePoint(coord.Coord):
	def __init__(self, x, y, unique_id):
		super(CoveragePoint, self).__init__(x, y)
		self.__id = unique_id


class CoveragePointsMapManager(StrategicPointsMapManager):

	def __init__(self, mapworld, fps, velocity, num_rays, visibility_angle, offset = 10, inference_map=True):
		super(CoveragePointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		self.__visibility_graph = nx.Graph()
		self.__coverage_points = []
		# self.__strategic_point_cells = [self.get_cell_from_coord(stp) for stp in self._strategic_points]
		# self.__strategic_visibility= [[] for stp in self._strategic_points]
		self.__add_visibility_nodes()
		# self.__strategic_visibility_set = [set(self.__strategic_visibility[i]) for i in range(self._num_strategic_points)]
		self.__add_visibility_edges()
		
		self.__print_nodes()

		self.__find_coverage_points()

	def __add_visibility_nodes(self):
		strategic_visibility = []
		for i in range(self._num_strategic_points):
			stp = self._strategic_points[i]
			visibility_polygon = self.get_360_visibility_polygon(stp)
			# print('')
			del strategic_visibility[:]
			# print('Strategic point:', stp.get_x(), stp.get_y())
			# print('Visibility polygon:', str(visibility_polygon))
			bbox = self._mapworld.get_bbox(stp).get_rtree_bbox()
			# print('BBOX:', bbox)
			common_boxes = [box.object for box in self._visibility_idx.intersection(bbox, objects=True)]
			# print('Common boxes for point:', stp.get_x(), stp.get_y(),len(common_boxes))
			for a,b in common_boxes:
				box_coord = self.get_coord_from_cell(a, b)
				# print('Box coord:', str(box_coord))
				if visibility_polygon.is_point_inside(box_coord):
					# self.__strategic_visibility[i].append((a,b))
					strategic_visibility.append((a,b))
			# print('Actually visible:', len(strategic_visibility))
			# print('Cells:', strategic_visibility)
			stp.set_visible_cells_set(set(strategic_visibility))
			self.__visibility_graph.add_node(i)

	def __add_visibility_edges(self):
		#Finding common cells
		for i in range(self._num_strategic_points):
			for j in range(i+1, self._num_strategic_points):
				pt1 = self._strategic_points[i]
				pt2 = self._strategic_points[j]
				visible_cells1 = pt1.get_visible_cells_set()
				visible_cells2 = pt2.get_visible_cells_set()
				common_cells = visible_cells1.intersection(visible_cells2)
				num_common_cells = len(common_cells)
				if num_common_cells > 1:
					self.__visibility_graph.add_edge(i, j)
					pt1.set_common_strategic_point(j, num_common_cells)
					pt2.set_common_strategic_point(i, num_common_cells)

	def __print_nodes(self):
		#Printing strategic points
		for i in range(self._num_strategic_points):
			# print('Strategic Point:',i, str(self._strategic_points[i]))
			print('St pt:', i,'points adjacent to it:', list(self.__visibility_graph.neighbors(i)))
		# print('Number of nodes:', self.__visibility_graph.number_of_nodes())
		# print('Nodes:', list(self.__visibility_graph.nodes()))
		# print('Number of edges:', self.__visibility_graph.number_of_edges())
		# print('Edges:', list(self.__visibility_graph.edges()))

	def __get_cliques_coverage_point(self, clique):
		coverage_point = None
		cid = clique[0]
		cst_pt = self._strategic_points[cid]
		if len(clique) > 1:
			cvisible_cells = cst_pt.get_visible_cells_set()
			coverage_point = None
			for cell in cvisible_cells:
				cell_coord = self.get_coord_from_cell(cell[0], cell[1])
				visibility_polygon = self.get_360_visibility_polygon(cell_coord, 100)
				all_flag = True
				for node in clique:
					cst_adj_pt = self._strategic_points[node]
					if not visibility_polygon.is_point_inside(cst_adj_pt):
						all_flag = False
						break

				if all_flag == True:
					coverage_point = cell_coord
					break
		else:
			coverage_point = cst_pt
		return coverage_point

	def __mark_cliques_nodes(self, clique):
		for node in clique:
			cst_pt = self._strategic_points[node]
			if not cst_pt.is_covered():
				print('Marking node:', node)
				cst_pt.mark_covered()

	def __check_all_marked(self, clique):
		for node in clique:
			cst_pt = self._strategic_points[node]
			if not cst_pt.is_covered():
				print('Node:', node,' is not marked')
				return False
		return True

	def __find_coverage_points(self):
		print('Cliques:')
		cliques = list(nx.find_cliques(self.__visibility_graph))
		cliques.sort(key=len, reverse=True)
		print('Total number of maximal cliques:', len(cliques))
		for clique in (cliques):
			print(clique)
			# all_marked = self.__check_all_marked(clique)
			# if not all_marked:
			# print('X Not all nodes where marked')
			coverage_point = self.__get_cliques_coverage_point(clique)
			assert(coverage_point != None)
			# self.__mark_cliques_nodes(clique)
			print('Coverage point:', str(coverage_point))
			self.__coverage_points.append(coverage_point)
			# else:
			# 	print('* All marked')









