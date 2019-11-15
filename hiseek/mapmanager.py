import math
import os
import pickle
import random
import collections
import json
from abc import ABCMeta, abstractmethod

import numpy as np
import cvxpy as cp
import rtree
import matplotlib.pyplot as plt
import networkx as nx

import gamemap
import coord
import action
import shapes

class BasicMapManager(object):
	'''
		Each agent is associated with a map manager which helps it to manage
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
		self.__inference_map = inference_map
		self._map_name = mapworld.get_map_name().split('.')[0]

		vis_file = self._map_name + '.visibility'
		obs_file = self._map_name + '.obstruction'
		idx_file = self._map_name + '.index'
		if self.__inference_map:
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
				####
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

				np.savetxt(self._map_name.split('.')[0] + '.visibility',self._visibility)
				np.savetxt(self._map_name.split('.')[0] + '.obstruction', self._obstruction)
				####
				self._visibility_idx.close()
				# Reinitializing idx since .close() makes the idx unusable
				self._visibility_idx = rtree.index.Index(idx_file)


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

	def get_map_name(self):
		return self._map_name

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

	def get_all_coords_from_cell(self, row, col):
		'''
			Returns the coordinates corresponding to the centre and all the corners
			of the cell.
		'''
		cell_coords = []
		x = int(row * self.__offset - self.__offset/2)
		y = int(col * self.__offset - self.__offset/2)
		cell_coords.append(coord.Coord(x, y))

		ofsetters = [(-1,-1), (0,-1), (-1,0), (0, 0)]
		for of in ofsetters:
			x = int((row - of[0]) * self.__offset)
			y = int((col - of[1]) * self.__offset)
			cell_coords.append(coord.Coord(x, y))

		return cell_coords



class StrategicPointsMapManager(BasicMapManager):

	def __init__(self, mapworld, fps, velocity, offset = 10, inference_map=True):
		'''
			threshold: Strategic points which have a distance less than the 
					   threshold will be merged into one.
		'''
		super(StrategicPointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		all_strtg_pts = []
		self.__threshold = 50
		self._strategic_points = None
		self.__strategic_pts_idx = None

		self.__sp_file = self._map_name + '.st_pts'
		self.__sp_idx_file = self._map_name + '.st_pts_index'


		if os.path.isfile(self.__sp_file) and os.path.isfile(self.__sp_idx_file + '.idx'):
			print('Loading startegic files')
			self.__load_strategic_points()
			self.__load_strategic_points_index()
		else:
			print('Creating strategic files')
			self._strategic_points = []
			p = rtree.index.Property()
			# print('overwrite then:', p.overwrite)
			p.overwrite = True
			# print('overwrite now:', p.overwrite)

			self.__strategic_pts_idx = rtree.index.Index(self.__sp_idx_file, properties=p)

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

			self.__store_strategic_points()
			self.__store_strategic_points_index()
			

		self._num_strategic_points = len(self._strategic_points)
		print('* Number of strategic points:{}'.format(self._num_strategic_points))

		# TO DO: Merge strategic points if they are very close to each other and
		# there is no obstacle between them

	def __store_strategic_points(self):
		spfile = open(self.__sp_file, 'wb')
		# for stp in self._strategic_opints:
		pickle.dump(self._strategic_points, spfile, pickle.HIGHEST_PROTOCOL)
		spfile.close()

	def __store_strategic_points_index(self):
		self.__strategic_pts_idx.close()
		# .close() makes the st pt inaccessible, therefore reopening it
		self.__strategic_pts_idx = rtree.index.Index(self.__sp_idx_file)


	def __load_strategic_points(self):
		spfile = open(self.__sp_file, 'rb')
		self._strategic_points = pickle.load(spfile)

	def __load_strategic_points_index(self):
		self.__strategic_pts_idx = rtree.index.Index(self.__sp_idx_file)



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
		if len(closest_st_pts) > num_points:
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

	def __str__(self):
		point_string = '('+ str(self.get_x()) + ':' + str(self.get_y()) + '); ' + 'Common strategic points:' + str(self.__common_strategic_points) +' Number common cells:' + str(self.__num_cells_common) 
		return point_string

class CoveragePoint(coord.Coord):
	def __init__(self, x, y, unique_id, clique):
		super(CoveragePoint, self).__init__(x, y)
		self.__id = unique_id
		self.__clique = clique
		self.__explored = False

	def is_explored(self):
		return self.__explored

	def mark_explored(self):
		self.__explored = True

	def get_id(self):
		return self.__id

	def get_clique(self):
		return self.__clique


class CoveragePointsMapManager(StrategicPointsMapManager):

	def __init__(self, mapworld, fps, velocity, num_rays, visibility_angle, offset = 10, inference_map=True, redo=False):
		super(CoveragePointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		print('Loading CoveragePointsMapManager')
		self.__visibility_graph = nx.Graph()
		self.__coverage_graph = nx.Graph()
		self._cliques = []
		self.__strategic_points2cliques = [[] for stp in self._strategic_points]
		
		self.__num_rays = num_rays * 4
		print('Num rays used:', self.__num_rays)

		self._coverage_points = None
		self._coverage_pts_idx = None
		self._coverage_contours = None
		self.__coverage_point2contour = None

		self.__cp_file = self._map_name + '.cpts'
		self.__cp_idx_file = self._map_name + '.cpts_index'
		self.__contours_file = self._map_name + '.contours'
		# also coverage pt 2 contour

		if not redo and os.path.isfile(self.__cp_file) and os.path.isfile(self.__cp_idx_file + '.idx') and os.path.isfile(self.__contours_file):
			print('Loading coverage point files')
			self.__load_coverage_points()
			self.__load_coverage_points_index()
			self.__load_coverage_contours()
		else:
			self._coverage_points = []
			self._coverage_pts_idx = rtree.index.Index(self.__cp_idx_file)
			self._coverage_contours = []

			self.__create_visibility_graph()
			# self.__print_visibility_graph()
			self.__find_coverage_points()
			self.__associate_strategic_points2cliques()
			self.__create_coverage_graph()
			# self.__print_coverage_graph()
			self.__save_visibility_graph_plot()
			self.__save_coverage_graph_plot()
			self.__get_coverage_contours()

			self.__store_coverage_points()
			self.__store_coverage_points_index()
			self.__store_coverage_contours()
		
		print('* Number of coverage points:{}'.format(len(self._coverage_points)))
		# print('Coverage points:', self._coverage_points)
		# print('Coverage contours:', self._coverage_contours)

		self.__associate_coverage_point2contours()

	def get_num_coverage_points(self):
		return len(self._coverage_points)

	def get_coverage_point(self, uid):
		return self._coverage_points[uid]

	def get_coverage_points(self):
		return self._coverage_points

	def get_num_coverage_contours(self):
		return len(self._coverage_contours)

	def get_coverage_contour(self, uid):
		return self._coverage_contours[uid]

	def get_coverage_contours(self):
		return self._coverage_contours

	def get_coverage_contour_from_point(self, coverage_point_id):
		contour_id = self.__coverage_point2contour[coverage_point_id]
		contour = self._coverage_contours[contour_id]
		return contour

	def get_coverage_contour_id_from_point(self, coverage_point_id):
		contour_id = self.__coverage_point2contour[coverage_point_id]
		return contour_id

	def get_closest_coverage_point(self, point, num_points = 1):
		cx = point.get_x()
		cy = point.get_y()
		bound_box = (cx, cy, cx, cy)
		closest_coverage_pts = list(self._coverage_pts_idx.nearest(bound_box, num_points))
		# print('Closest points:', closest_coverage_pts)
		if len(closest_coverage_pts) != num_points:
			closest_coverage_pts = list(np.random.choice(closest_coverage_pts, num_points, replace=False))
		return closest_coverage_pts

	def get_strategic_point_clique_ids(self, strategic_point_id):
		print(self.__strategic_points2cliques)
		return self.__strategic_points2cliques[strategic_point_id]

	def get_clique(self, coverage_point_id):
		return self._cliques[coverage_point_id]

	def __store_coverage_points(self):
		cpfile = open(self.__cp_file, 'wb')
		pickle.dump(self._coverage_points, cpfile, pickle.HIGHEST_PROTOCOL)
		cpfile.close()

	def __store_coverage_points_index(self):
		self._coverage_pts_idx.close()
		# .close() makes the cpt idx inaccessible, therefore reopening it
		self._coverage_pts_idx = rtree.index.Index(self.__cp_idx_file)

	def __store_coverage_contours(self):
		ccfile = open(self.__contours_file, 'wb')
		print('Storing coverage contours:', self._coverage_contours)
		pickle.dump(self._coverage_contours, ccfile, pickle.HIGHEST_PROTOCOL)
		ccfile.close()

	def __load_coverage_points(self):
		cpfile = open(self.__cp_file, 'rb')
		self._coverage_points = pickle.load(cpfile)

	def __load_coverage_points_index(self):
		self._coverage_pts_idx = rtree.index.Index(self.__cp_idx_file)

	def __load_coverage_contours(self):
		ccfile = open(self.__contours_file, 'rb')
		self._coverage_contours = pickle.load(ccfile)

	def __create_visibility_graph(self):
		self.__add_visibility_nodes()
		self.__add_visibility_edges()

	def __add_visibility_nodes(self):
		strategic_visibility = []
		for i in range(self._num_strategic_points):
			stp = self._strategic_points[i]
			visibility_polygon = self.get_360_visibility_polygon(stp, 40)
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

	def __print_visibility_graph(self):
		#Printing strategic points
		for i in range(self._num_strategic_points):
			print('Strategic Point:',i, str(self._strategic_points[i]))
			print('St pt:', i,'points adjacent to it:', list(self.__visibility_graph.neighbors(i)))
		print('Number of nodes:', self.__visibility_graph.number_of_nodes())
		print('Nodes:', list(self.__visibility_graph.nodes()))
		print('Number of edges:', self.__visibility_graph.number_of_edges())
		print('Edges:', list(self.__visibility_graph.edges()))

	def __get_cliques_coverage_points(self, clique):
		'''
			Returns the coverage points corresponding to a clique
		'''
		coverage_points = []
		coverage_point = None
		cid = clique[0]
		cst_pt = self._strategic_points[cid]

		nodes_covered = []
		num_nodes_covered = 0
		max_nodes_covered = []
		num_max_nodes_covered = 0
		max_cov_coord = None

		coverage_cliques = []

		if len(clique) > 1:
			cvisible_cells = cst_pt.get_visible_cells_set()
			coverage_point = None
			for cell in cvisible_cells:
				cell_coord = self.get_coord_from_cell(cell[0], cell[1])
				visibility_polygon = self.get_360_visibility_polygon(cell_coord, 300)
				all_flag = True

				del nodes_covered[:]
				num_nodes_covered = 0

				for node in clique:
					cst_adj_pt = self._strategic_points[node]
					if not visibility_polygon.is_point_inside(cst_adj_pt):
						all_flag = False
						# break
					else:
						nodes_covered.append(node)

				num_nodes_covered = len(nodes_covered)
				if num_nodes_covered > num_max_nodes_covered:
					max_nodes_covered = nodes_covered
					num_max_nodes_covered = num_nodes_covered
					max_cov_coord = cell_coord

				if all_flag == True:
					coverage_point = cell_coord
					break
		else:
			max_nodes_covered.append(cid)
			num_max_nodes_covered = 1
			coverage_point = cst_pt
		
		print('Max nodes covered:', max_nodes_covered)

		if coverage_point == None:
			coverage_points.append(max_cov_coord)
			coverage_cliques.append(max_nodes_covered)


			remaining_clique = []
			for node in clique:
				if node not in max_nodes_covered:
					remaining_clique.append(node)
			remaining_coverage_points, remaining_coverage_cliques = self.__get_cliques_coverage_points(remaining_clique)
			for cov_pts in remaining_coverage_points:
				coverage_points.append(cov_pts)
			for coverage_clique in remaining_coverage_cliques:
				coverage_cliques.append(coverage_clique)

		else:
			coverage_points.append(coverage_point)
			coverage_cliques.append(max_nodes_covered)
		
		print('Coverage points:')
		for cov_pt in coverage_points:
			print(str(cov_pt))
		return coverage_points, coverage_cliques



		# if coverage_point == None:
		# 	print('Searching intensively')
		# 	cvisible_cells = cst_pt.get_visible_cells_set()
		# 	coverage_point = None
		# 	for cell in cvisible_cells:
		# 		cell_coords = self.get_all_coords_from_cell(cell[0], cell[1])
		# 		for cell_coord in cell_coords:
		# 			visibility_polygon = self.get_360_visibility_polygon(cell_coord, 300)
		# 			all_flag = True
		# 			for node in clique:
		# 				cst_adj_pt = self._strategic_points[node]
		# 				if not visibility_polygon.is_point_inside(cst_adj_pt):
		# 					all_flag = False
		# 					break

		# 			if all_flag == True:
		# 				coverage_point = cell_coord
		# 				return coverage_point
		# 				# break


	def __mark_cliques_nodes(self, clique):
		for node in clique:
			cst_pt = self._strategic_points[node]
			if not cst_pt.is_covered():
				# print('Marking node:', node)
				cst_pt.mark_covered()

	def __check_all_marked(self, clique):
		for node in clique:
			cst_pt = self._strategic_points[node]
			if not cst_pt.is_covered():
				# print('Node:', node,' is not marked')
				return False
		return True

	def __find_coverage_points(self):
		print('Cliques:')
		clique_list = list(nx.find_cliques(self.__visibility_graph))
		clique_list.sort(key=len, reverse=True)
		total_sts_covered = 0

		counter = 0
		for clique in clique_list:
			print('')
			print(clique)
			coverage_points, coverage_cliques = self.__get_cliques_coverage_points(clique)
			# for coverage_point in coverage_points:
			for i in range(len(coverage_points)):
				coverage_point = coverage_points[i]
				coverage_clique = coverage_cliques[i]
				assert(coverage_point != None)
				print('* Coverage point:', str(coverage_point))
				print('* Coverage clique:', str(coverage_clique))
				coverage_point = CoveragePoint(coverage_point.get_x(), coverage_point.get_y(), counter, coverage_clique)
				cx = coverage_point.get_x()
				cy = coverage_point.get_y()
				bound_box = (cx, cy, cx, cy)
				self._coverage_pts_idx.insert(counter, bound_box, obj=counter)
				self._coverage_points.append(coverage_point)
				self._cliques.append(coverage_clique)
				total_sts_covered += len(coverage_clique)
				counter += 1
		print('Strategic points:')
		for i in range(len(self._strategic_points)):
			print(i,':',str(self._strategic_points[i]))
		print('')
		print('Coverage points:', self._coverage_points)
		for i in range(len(self._coverage_points)):
			print(i,':',str(self._coverage_points[i]))
		print('Total number of coverage points:', len(self._coverage_points))
		print('Total strategic points:', len(self._strategic_points))
		print('Average strategic points covered:', total_sts_covered*1.0/len(self._coverage_points))

	def __associate_strategic_points2cliques(self):
		for i in range(len(self._cliques)):
			clique = self._cliques[i]
			for stp_id in clique:
				self.__strategic_points2cliques[stp_id].append(i)
		# for i in range(len(self._cliques)):
		# 	clique = self._cliques[i]
		# 	print('Clique:', i, 'associated strategic points:', clique)
		# print()
		# for i in range(len(self._strategic_points)):
		# 	print('Strategic Point:',i, 'Associated cliques:', self.__strategic_points2cliques[i])

	def __create_coverage_graph(self):
		self.__add_coverage_nodes()
		self.__add_coverage_edges()

	def __add_coverage_nodes(self):
		for coverage_point in self._coverage_points:
			print('i:', str(coverage_point))
			self.__coverage_graph.add_node(coverage_point.get_id())

	def __add_coverage_edges(self):
		for coverage_point in self._coverage_points:
			if not coverage_point.is_explored():
				self.__explore_coverage_point(coverage_point)

	def __explore_coverage_point(self, coverage_point):
		clique_limit = 2
		coverage_point.mark_explored()
		clique = coverage_point.get_clique()
		# print('Coverage point:', str(coverage_point), ' clique:', clique)
		for stp_id in clique:
			adjacent_clique_ids = self.__strategic_points2cliques[stp_id]
			# Since each clique has a one-one map to a coverage point
			adjacent_coverage_point_ids = adjacent_clique_ids
			for ad_id in adjacent_coverage_point_ids:
				adjacent_coverage_point = self._coverage_points[ad_id]
				adjacent_clique = self._cliques[ad_id]
				# print('Edge')
				# print('Clique set:', set(clique))
				# print('Adjacent clique set:', set(adjacent_clique))
				clique_intersection = set(clique).intersection(set(adjacent_clique))
				if not adjacent_coverage_point.is_explored() and len(clique_intersection) >= clique_limit:
					self.__coverage_graph.add_edge(coverage_point.get_id(), adjacent_coverage_point.get_id())

	def __print_coverage_graph(self):
		print('Coverage nodes:', self.__coverage_graph.nodes())
		print('Coverage edges:', self.__coverage_graph.edges())

	def __get_coverage_contours(self):
		coverage_subgraphs = nx.connected_component_subgraphs(self.__coverage_graph)
		for subgraph in coverage_subgraphs:
			contour = list(nx.dfs_preorder_nodes(subgraph))
			self._coverage_contours.append(contour)
			print('Contour:', contour)

	def __associate_coverage_point2contours(self):
		num_contours = len(self._coverage_contours)
		num_coverage_points = len(self._coverage_points)
		self.__coverage_point2contour = [None for i in range(num_coverage_points)]
		for i in range(num_contours):
			contour = self._coverage_contours[i]
			for coverage_point in contour:
				self.__coverage_point2contour[coverage_point] = i
		# for i in range(num_coverage_points):
		# 	print('Coverage point:', i, 'is associated with contour:', self.__coverage_point2contour[i])

	def __save_visibility_graph_plot(self):
		plt.clf()
		nx.draw(self.__visibility_graph)
		plt.savefig(self._map_name + '_visibility_graph.png')
		print('Visibility Graph saved')

	def __save_coverage_graph_plot(self):
		plt.clf()
		nx.draw(self.__coverage_graph)
		plt.savefig(self._map_name +'_coverage_graph.png')
		print('Coverage Graph saved')


class OffsetPoint(coord.Coord):
	
	def __init__(self, pnt_id, x, y):
		super(OffsetPoint, self).__init__(x, y)
		self.__pnt_id = pnt_id

	def get_point_id(self):
		return self.__pnt_id

class OffsetPointRectangle(OffsetPoint):

	def __init__(self, pnt_id, x, y, point_action):
		super(OffsetPointRectangle, self).__init__(pnt_id, x, y)
		self.__point_action = point_action

	def get_point_action(self):
		return self.__point_action


class OffsetPointCircle(OffsetPoint):

	def __init__(self, pnt_id, x, y, point_action_clkwise, point_action_anti_clkwise):
		super(OffsetPointCircle, self).__init__(pnt_id, x, y)
		self.__point_action_clkwise = point_action_clkwise
		self.__point_action_anti_clkwise = point_action_anti_clkwise

	def get_point_action_clkwise(self):
		return self.__point_action_clkwise

	def get_point_action_anti_clkwise(self):
		return self.__point_action_anti_clkwise

class OffsetObstacle(object):
	def __init__(self, obs_id, polygon):
		self.__obs_id = obs_id
		self._polygon = polygon
		self._offset_points = []

	def get_count_offset_points(self):
		return len(self._offset_points)

	def get_obstacle_id(self):
		return self.__obs_id

	def get_polygon(self):
		return self._polygon

	def get_offset_point(self, pnt_id):
		assert(pnt_id < len(self._offset_points))
		return self._offset_points[pnt_id]

class OffsetObstacleRectangle(OffsetObstacle):

	def __init__(self, obs_id, polygon, horizontal_gap, vertical_gap):
		super(OffsetObstacleRectangle, self).__init__(obs_id, polygon)
		self.__horizontal_gap = horizontal_gap
		self.__vertical_gap = vertical_gap
		self.__left_edge = self._polygon.get_left_edge()
		self.__right_edge = self._polygon.get_right_edge()
		self.__top_edge = self._polygon.get_top_edge()
		self.__bottom_edge = self._polygon.get_bottom_edge()

		self.__extract_offset_points()
		
	def __append_offset_point(self, x, y, x_factor, y_factor, point_action):
		x_offset = x_factor * self.__horizontal_gap
		y_offset = y_factor * self.__vertical_gap
		offx, offy = x + x_offset, y + y_offset
		offset_point = OffsetPointRectangle(len(self._offset_points), offx, offy, point_action)
		self._offset_points.append(offset_point)

	def __extract_offset_points(self):
		
		self.__append_offset_point(self.__left_edge, self.__top_edge, 1, 1, action.Action.W)
		self.__append_offset_point(self.__right_edge, self.__top_edge, -1, 1, action.Action.E)
		self.__append_offset_point(self.__right_edge, self.__top_edge, 1, -1, action.Action.N)
		self.__append_offset_point(self.__right_edge, self.__bottom_edge, 1, 1, action.Action.S)
		self.__append_offset_point(self.__right_edge, self.__bottom_edge, -1, -1, action.Action.E)
		self.__append_offset_point(self.__left_edge, self.__bottom_edge, 1, -1, action.Action.W)
		self.__append_offset_point(self.__left_edge, self.__bottom_edge, -1, 1, action.Action.S)
		self.__append_offset_point(self.__left_edge, self.__top_edge, -1, -1, action.Action.N)

	def get_hiding_offset_point(self, offset_point):
		pnt_id = offset_point.get_point_id()
		idx = None
		if pnt_id % 2 == 0:
			idx = (pnt_id + 2) % len(self._offset_points)
		else:
			idx = pnt_id - 2
			if idx < 0:
				idx += len(self._offset_points)
		return self._offset_points[idx]

class OffsetObstacleCircle(OffsetObstacle):
	
	def __init__(self, obs_id, polygon, radial_gap):
		super(OffsetObstacleCircle, self).__init__(obs_id, polygon)
		self.__radial_gap = radial_gap
		self.__radius = self._polygon.get_radius()
		self.__centre_tuple = self._polygon.get_centre()

		self.__extract_offset_points()

	def __append_offset_point(self, direction):
		radial_vector = action.VECTOR[direction].multiply_scalar(self.__radius + self.__radial_gap)
		x = radial_vector.get_x_component() + self.__centre_tuple[0]
		y = radial_vector.get_y_component() + self.__centre_tuple[1]
		point_action = action.OBLIQUE_DIR_CLOCKWISE[direction]
		alt_point_action = action.OBLIQUE_DIR_ANTI_CLOCKWISE[direction]
		offset_point = OffsetPointCircle(len(self._offset_points), x, y, point_action, alt_point_action)
		self._offset_points.append(offset_point)

	def __extract_offset_points(self):
		for direction in action.Action.all_directions:
			self.__append_offset_point(direction)

	def get_hiding_offset_point(self, offset_point, direction):
		pnt_id = offset_point.get_point_id()
		idx = None
		if direction == offset_point.get_point_action_clkwise():
			idx = pnt_id - 4
			if idx < 0:
				idx += len(self._offset_points)
		elif direction == offset_point.get_point_action_anti_clkwise():
			idx = (pnt_id + 4) % len(self._offset_points)
		return self._offset_points[idx]


class OffsetPointsMapManager(BasicMapManager):

	def __init__(self, mapworld, fps, velocity, offset = 10, inference_map=True):
		super(OffsetPointsMapManager, self).__init__(mapworld, fps, velocity, offset, inference_map)
		self.__offset_obstacles = []
		self.__obstacle_graph = nx.Graph()
		self.__obstacles_explored = []
		self.__horizontal_gap = 5
		self.__vertical_gap = 5
		self.__radial_gap = 5
		self.__graph_edge_gap = 40

		self.__add_offset_obstacles()
		self.__create_obstacle_graph()

	def __add_offset_obstacles(self):
		num_obstacles = self._mapworld.get_num_polygons()
		for idx in range(num_obstacles):
			polygon = self._mapworld.get_polygon(idx)
			offset_obstacle = None
			# A square type polygon will also be an instance of Rectangle
			obs_id = len(self.__offset_obstacles)
			if isinstance(polygon, shapes.Rectangle):
				offset_obstacle = OffsetObstacleRectangle(obs_id, polygon, self.__horizontal_gap, self.__vertical_gap)
			elif isinstance(polygon, shapes.Circle):
				offset_obstacle = OffsetObstacleCircle(obs_id, polygon, self.__radial_gap)
			self.__offset_obstacles.append(offset_obstacle)

	def __get_nearby_obstacle_ids(self, idx):
		polygon = self.__offset_obstacles[idx].get_polygon()
		centre_tuple = polygon.get_centre()
		width = polygon.get_width() + self.__graph_edge_gap
		height = polygon.get_height() + self.__graph_edge_gap
		bound_rect = shapes.Rectangle(centre_tuple, width, height)
		nearby_obs_ids = self._mapworld.get_intersected_polygon_ids(bound_rect)
		return nearby_obs_ids

	def __create_obstacle_graph(self):
		num_obstacles = len(self.__offset_obstacles)
		for idx in range(num_obstacles):
			self.__obstacle_graph.add_node(idx)
			self.__obstacles_explored.append(False)

		for idx in range(num_obstacles):
			if self.__obstacles_explored[idx] == False:
				print('* Expanding graph')
				self.__expand_obstacle_graph(idx)

	def __expand_obstacle_graph(self, idx):
		self.__obstacles_explored[idx] = True
		print('* Node {} added'.format(idx))
		nearby_obstacle_ids = self.__get_nearby_obstacle_ids(idx)
		for nid in nearby_obstacle_ids:
			# networkx graph library ignores duplicate edges
			self.__obstacle_graph.add_edge(idx, nid)
			if self.__obstacles_explored[nid] == False:
				self.__expand_obstacle_graph(nid)

	def get_offset_obstacle(self, idx):
		assert(idx < len(self.__offset_obstacles))
		return self.__offset_obstacles[idx]

	def get_count_offset_obstacles(self):
		return len(self.__offset_obstacles)

	def get_random_adjacent_obstacle(self, offset_obstacle):
		obs_id = offset_obstacle.get_obstacle_id()
		neighbor_ids = self.__obstacle_graph.neighbors(obs_id)
		random_idx = random.randint(0, len(neighbor_ids)-1)
		random_obs_id = neighbor_ids[random_idx]
		return self.get_offset_obstacle(random_obs_id)

	# def get_offset_obstacle_point(self, obs_id, pnt_id):
	# 	obstacle = self.get_offset_obstacle(obs_id)
	# 	offset_point = obstacle.get_offset_point(pnt_id)
	# 	return offset_point

	# def get_offset_obstacle_point_coord(self, obs_id, pnt_id):
	# 	offset_point = self.get_offset_obstacle_point(obs_id, pnt_id)
	# 	return offset_point.get_offset_coord()

class HikerGraphComponent(object):
	def __init__(self, map_manager, idx, strategic_node_set=None):

		self._strategic_node_set = strategic_node_set
		self._map_manager = map_manager
		self._map_name = map_manager.get_map_name()

		self._cap_graph_file = self._map_name + '_' + str(idx) + '_.cap_graph'

		self._capture_graph = None
		
	def _find_coverage_nodes(self):
		coverage_node_set = set()
		for strat_node in self._strategic_node_set:
			clique_ids = self._map_manager.get_strategic_point_clique_ids(strat_node)
			# clque id = cov_node id
			for cov_node in clique_ids:
				coverage_node_set.add(cov_node)
		print('	Found coverage nodes:{}'.format(coverage_node_set))
		return coverage_node_set

	def _fetch_capture_graph(self):
		if os.path.isfile(self._cap_graph_file):
			self._capture_graph = nx.read_gpickle(self._cap_graph_file)
		else:
			self._create_capture_graph()
			nx.write_gpickle(self._capture_graph, self._cap_graph_file)

	def _create_capture_graph(self):
		coverage_node_set = self._find_coverage_nodes()

		self._capture_graph = nx.Graph()
		for cov_node in coverage_node_set:
			self._capture_graph.add_node(cov_node)

		for cov_node in self._capture_graph:
			# clique id = coverage point id
			clique = self._map_manager.get_clique(cov_node)
			adj_strat_nodes = [x for x in clique if x in self._strategic_node_set]
			for strat_node in adj_strat_nodes:
				adj_cov_nodes = self._map_manager.get_trans_coverage_nodes(strat_node)
				adj_cov_nodes = [x for x in adj_cov_nodes if x in coverage_node_set]
				adj_cov_nodes = [x for x in adj_cov_nodes if x != cov_node]
				for adj_cov_node in adj_cov_nodes:
					self._capture_graph.add_edge(cov_node, adj_cov_node)

class WaveGraphComponent(HikerGraphComponent):

	def __init__(self, map_manager, idx, strategic_node_set=None):
		super(WaveGraphComponent, self).__init__(map_manager, idx, strategic_node_set)
		
		self.__cov_layer_file = self._map_name + '_' + str(idx) + '_.cov_layer'
		
		self._cov_node2layer = {}
		self.__coverage_layers = None
		self.__min_seekers = None

		# self._strat_node2layer = {}
		# self.__strategic_layers = None

		if os.path.isfile(self.__cov_layer_file):
			print('Hiker component cache FOUND, loading')
			self.__load_coverage_layers()
		else:
			print('Hiker component cache NOT FOUND, creating')
			self._fetch_capture_graph()
			self.__find_optimal_layers()
			self.__associate_covnodes2layers()
			self.__store_coverage_layers()

			# self.__associate_stratnodes2layers()

	def __capture_bfs(self, source_cov_node):
		explored = {cov_node: False for cov_node in self._capture_graph}
		q = collections.deque()

		q.append(source_cov_node)
		explored[source_cov_node] = True
		layers = []

		while q:
			n = len(q)
			layers.append([])
			for i in range(n):
				cur_cov_node = q.popleft()
				layers[-1].append(cur_cov_node)
				for cov_node in self._capture_graph.neighbors(cur_cov_node):
					if not explored[cov_node]:
						q.append(cov_node)
						explored[cov_node] = True
		return layers

	def __min_seekers_required(self, layers):
		max_sum = len(layers[0])
		current_sum = 0
		for i in range(1, len(layers)):
			current_sum = len(layers[i]) + len(layers[i-1])
			max_sum = max(max_sum, current_sum)
		return max_sum

	def __find_optimal_layers(self):
		self.__min_seekers = 100000000
		for cov_node in self._capture_graph:
			layers = self.__capture_bfs(cov_node)
			reqd_seekers = self.__min_seekers_required(layers)
			if reqd_seekers < self.__min_seekers:
				self.__coverage_layers = layers
				self.__min_seekers = reqd_seekers

	def __associate_covnodes2layers(self):
		for layer_id, layer in enumerate(self.__coverage_layers):
			for cov_node in layer:
				self._cov_node2layer[cov_node] = layer_id

	def __store_coverage_layers(self):
		clfile = open(self.__cov_layer_file, 'wb')
		print('Storing coverage layers:', self.__coverage_layers)
		pickle.dump(self.__coverage_layers, clfile, pickle.HIGHEST_PROTOCOL)
		clfile.close()

	def __load_coverage_layers(self):
		clfile = open(self.__cov_layer_file, 'rb')
		self.__coverage_layers = pickle.load(clfile)
		clfile.close()

	# def __associate_stratnodes2layers(self):
	# 	self.__strategic_layers = [[] for x in self.__coverage_layers]
	# 	for strat_node in self._strategic_node_set:
	# 		clique_ids = self._map_manager.get_strategic_point_clique_ids(strat_node)
	# 		layer_id = min([self._cov_node2layer[cov_node] for cov_node in clique_ids])
			
	# 		self._strat_node2layer[strat_node] = layer_id
	# 		self.__strategic_layers[layer_id].append(strat_node)

	# def get_layer_strategic_nodes(self, layer_id):
	# 	return self.__strategic_layers[layer_id]

	def get_layer_coverage_nodes(self, layer_id):
		return self.__coverage_layers[layer_id]

	def get_num_layer_coverage_nodes(self, layer_id):
		return len(self.__coverage_layers[layer_id])

	def get_num_layers(self):
		return len(self.__coverage_layers)

	def get_min_seekers(self):
		if self.__min_seekers is not None:
			return self.__min_seekers
		self.__min_seekers = self.__min_seekers_required(self.__coverage_layers)
		return self.__min_seekers

class TrapGraphComponent(HikerGraphComponent):

	def __init__(self, map_manager, idx, strategic_node_set=None):
		super(TrapGraphComponent, self).__init__(map_manager, idx, strategic_node_set)
		
		self.__trap_file = self._map_name + '_' + str(idx) + '_trap.json'
		self.__trap_occupancy = None

		if os.path.isfile(self.__trap_file):
			print('Trap component cache FOUND, loading')
			self.__load_trap_occupancies()
		else: 
			print('Trap component cache NOT FOUND, creating')

			self._fetch_capture_graph()

			self.__find_trap_occupancies()
			self.__store_trap_occupancies()

		print('* Occupied - Number:{}, Nodes{}, '.format(len(self.__trap_occupancy['occupied']), self.__trap_occupancy['occupied']))
		print('* Non Occupied - Number:{}, Nodes:{}'.format(len(self.__trap_occupancy['non_occupied']), self.__trap_occupancy['non_occupied']))


	def __get_adjacent_vector(self, coverage_nodes, cov_node):
		adj_vec = np.zeros(len(coverage_nodes), dtype=int)
		for idx, cur_cov_node in enumerate(coverage_nodes):
			if cur_cov_node in self._capture_graph.neighbors(cov_node):
				adj_vec[idx] = 1
		return adj_vec

	def __find_trap_occupancies(self):
		coverage_nodes = sorted(list(self._capture_graph))
		print('** Coverage Nodes:{}'.format(coverage_nodes))
		selection = cp.Variable(len(coverage_nodes), boolean=True)
		constraints = []
		for idx, cov_node in enumerate(coverage_nodes):
			adj_vec = self.__get_adjacent_vector(coverage_nodes, cov_node)
			degree = np.sum(adj_vec)
			constraint = adj_vec * selection >= ((1 - selection[idx]) * degree)
			constraints.append(constraint)

		objective = cp.Minimize(cp.sum(selection))

		opt_problem = cp.Problem(objective, constraints)
		print('Solving TRAP IP')
		opt_problem.solve(solver='GLPK_MI')
		print('Solution:{}'.format(selection.value))

		assert(selection.value is not None)

		self.__trap_occupancy = {'occupied':[], 'non_occupied':[]}
		for idx, cov_node in enumerate(coverage_nodes):
			if int(round(selection.value[idx])) == 1:
				self.__trap_occupancy['occupied'].append(cov_node)
			else:
				self.__trap_occupancy['non_occupied'].append(cov_node)

	def __store_trap_occupancies(self):
		with open(self.__trap_file, "w") as write_file:
			json.dump(self.__trap_occupancy, write_file)

	def __load_trap_occupancies(self):
		with open(self.__trap_file, "r") as read_file:
			self.__trap_occupancy = json.load(read_file)

	def get_occupied_nodes(self):
		return self.__trap_occupancy['occupied']

	def get_non_occupied_nodes(self):
		return self.__trap_occupancy['non_occupied']

	def get_num_occupied_nodes(self):
		return len(self.__trap_occupancy['occupied'])


class HikerMapManager(CoveragePointsMapManager):

	__metaclass__ = ABCMeta

	def __init__(self, mapworld, fps, velocity, num_rays, visibility_angle, offset = 10, inference_map=True):
			# We find mapname in this manner since we have tet to initialize the 
			# parent map manager classes
			map_name = mapworld.get_map_name().split('.')[0]
			self.__htrav_graph_file = map_name + '_.htrav_graph'
			self.__htrav_map_file = map_name + '_.htrav_map'

			redo = not (os.path.isfile(self.__htrav_graph_file) and os.path.isfile(self.__htrav_map_file))

			super(HikerMapManager, self).__init__(mapworld, fps, velocity, num_rays, visibility_angle, offset, inference_map, redo)
			self._components = []

			if redo:
				print('Hiker cached data NOT FOUND, reconstructing')
				self._htrav_graph = nx.Graph()
				self.__strat_node2adj_cov_nodes = [set() for i in range(self._num_strategic_points)]
				
				self.__create_htrav_graph()
				self.__associate_strats2adjacent_covs()

				self.__store_hiker_state()
			else:
				self.__load_hiker_state()
			self._create_components()

	def __create_htrav_graph(self):
		for strat_node in range(self._num_strategic_points):
			self._htrav_graph.add_node(strat_node)
			strat_pt = self._strategic_points[strat_node]
			adj_strat_nodes = self.get_closest_strategic_point(strat_pt, 4)
			adj_strat_nodes = [x for x in adj_strat_nodes if x != strat_node]
			print('Node:{} Adj Nodes:{}'.format(strat_node, adj_strat_nodes))
			for adj_strat_node in adj_strat_nodes:
				self._htrav_graph.add_edge(strat_node, adj_strat_node)

	def __associate_strats2adjacent_covs(self):
		for strat_node in self._htrav_graph:
			for adj_st_node in self._htrav_graph.neighbors(strat_node):
				# clique id = coverage point id
				for adj_cov_id in self.get_strategic_point_clique_ids(adj_st_node):
					self.__strat_node2adj_cov_nodes[strat_node].add(adj_cov_id)

	def get_trans_coverage_nodes(self, strat_node):
		return self.__strat_node2adj_cov_nodes[strat_node]

	def __store_hiker_state(self):
		f = open(self.__htrav_map_file, 'wb')
		pickle.dump(self.__strat_node2adj_cov_nodes, f, pickle.HIGHEST_PROTOCOL)
		f.close()
		
		nx.write_gpickle(self._htrav_graph, self.__htrav_graph_file)

	def __load_hiker_state(self):
		f = open(self.__htrav_map_file, 'rb')
		self.__strat_node2adj_cov_nodes = pickle.load(f)
		f.close()

		self._htrav_graph = nx.read_gpickle(self.__htrav_graph_file)

	@abstractmethod
	def _create_components(self):
		pass

	@abstractmethod
	def get_min_reqd_seekers(self):
		pass

	def get_component(self, component_id):
		return self._components[component_id]

	def get_num_components(self):
		return len(self._components)


class WaveMapManager(HikerMapManager):

	def __init__(self, mapworld, fps, velocity, num_rays, visibility_angle, offset = 10, inference_map=True):
			super(WaveMapManager, self).__init__(mapworld, fps, velocity, num_rays, visibility_angle, offset, inference_map)
			
	def _create_components(self):
		for idx, strat_node_set in enumerate(nx.connected_components(self._htrav_graph)):
			print('Connected component:{}'.format(strat_node_set))
			wave_component = WaveGraphComponent(self, idx, strat_node_set)
			self._components.append(wave_component)

	def get_min_reqd_seekers(self):
		'''
		Minimum number of seekers required for the strategy to work
		'''
		return max([comp.get_min_seekers() for comp in self._components])

class TrapMapManager(HikerMapManager):

	def __init__(self, mapworld, fps, velocity, num_rays, visibility_angle, offset = 10, inference_map=True):
			super(TrapMapManager, self).__init__(mapworld, fps, velocity, num_rays, visibility_angle, offset, inference_map)

	def _create_components(self):
		for idx, strat_node_set in enumerate(nx.connected_components(self._htrav_graph)):
			print('Connected component:{}'.format(strat_node_set))
			trap_component = TrapGraphComponent(self, idx, strat_node_set)
			self._components.append(trap_component)

	def get_min_reqd_seekers(self):
		'''
		Minimum number of seekers required for the strategy to work
		'''
		return max([comp.get_num_occupied_nodes() for comp in self._components]) + 1
