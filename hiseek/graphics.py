import math
import random 

import pyglet
from pyglet.window import key

import shapes
import coord
import gamemap
import action
import percept
import agent

class Player(pyglet.sprite.Sprite, key.KeyStateHandler):


	def __init__(self, img, batch, background, foreground, polygon_map, window_width, window_height, pos_x, pos_y, pos_rot, fps, velocity, fixed_time_quanta):
		super(Player, self).__init__(img, pos_x, pos_y, batch=batch, group=foreground)
		Player.center_anchor(img)
		self.scale = 0.5
		self.rotation = pos_rot
		self.dx = 0
		self.dy = 0
		self.rotation_x = 0
		self.rotation_y = 0
		self.__window_width = window_width
		self.__window_height = window_height
		self.__polygon_map = polygon_map
		self.__action = None
		self.__current_percept = percept.GraphicsPercept([],[],[],[])
		self.__prev_x = None
		self.__prev_y = None
		self.__prev_rotation = None
		self.__fps = fps
		self.__velocity = velocity
		self.__fixed_time_quanta = fixed_time_quanta

		# Visibility polygon setup
		self._num_rays = 10
		self._visibility_angle = 45
		# self._visibility_color = (149, 165, 166)
		self._visibility_color = 28, 40, 51  
		self._visibility_polygon = None

		self._num_vertices = self._num_rays + 1
		num_triangles = self._num_vertices - 2
		triangle_list = [0 for i in range(num_triangles * 3)]

		i = 1
		j = 1
		while i < num_triangles * 3:
			triangle_list[i] = j
			i += 3
			j += 1

		i = 2
		j = 2
		while i < num_triangles * 3:
			triangle_list[i] = j
			i += 3
			j += 1

		color_list = []
		for i in range(11):
			# 149, 165, 166
			color_list.append(self._visibility_color[0])
			color_list.append(self._visibility_color[1])
			color_list.append(self._visibility_color[2])
		color_tuple = tuple(color_list)
 
		self.__visibility_vertices = batch.add_indexed(self._num_vertices, pyglet.gl.GL_TRIANGLES, background, 
		triangle_list,
		('v2i', tuple([0 for i in range(self._num_vertices * 2)])),
		('c3B', color_tuple)
		)

	def remove(self):
		self.__visibility_vertices.vertices = [0 for i in range(self._num_vertices * 2)]
		self.__visibility_vertices.delete
		self.delete

	@staticmethod
	def center_anchor(img):
		img.anchor_x = img.width // 2
		img.anchor_y = img.height // 2

	def revert_configuration(self):
		self.x = self.__prev_x
		self.y = self.__prev_y
		self.rotation = self.__prev_rotation
		self.__update_visibility()

	def set_action(self, act):
		assert(act, action.Action)
		self.__action = act

	def get_action(self):
		return self.__action

	def set_visibility(self, visibility):
		self.visible = visibility

	def set_position(self, position):
		self.x = position.get_x()
		self.y = position.get_y()

	def set_position_raw(self, x, y):
		self.x = x
		self.y = y

	def set_rotation_raw(self, rotation):
		self.rotation = rotation

	def set_visibility_polygon_raw(self, points_tuple):
		self.__visibility_vertices.vertices = points_tuple

	def get_position(self):
		return coord.Coord(self.x, self.y)

	def get_visibility_polygon(self):
		return self._visibility_polygon

	def get_current_coordinate(self):
		return coord.Coord(self.x, self.y)

	def set_percept(self, current_percept):
		self.__current_percept = current_percept

	def get_percept(self):
		return self.__current_percept

	def update(self, dt):
		# Update rotation
		# print('Reached update:',dt)

		self.dx = 0
		self.dy = 0

		flag = False

		self.__prev_x = self.x
		self.__prev_y = self.y
		self.__prev_rotation = self.rotation

		if self.__action != action.Action.ST:
			self.rotation = action.ROTATION[self.__action]
			flag = True

		if self[key.NUM_6]:
			self.rotation = 0.1
			flag = True 
		elif self[key.NUM_3]:
			self.rotation = 45.1
			flag = True
		elif self[key.NUM_2]:
			self.rotation = 90.1
			flag = True
		elif self[key.NUM_1]:
			self.rotation = 135.1
			flag = True
		elif self[key.NUM_4]:
			self.rotation = 180.1
			flag = True
		elif self[key.NUM_7]:
			self.rotation = 225.1
			flag = True
		elif self[key.NUM_8]:
			self.rotation = 270.1
			flag = True
		elif self[key.NUM_9]:
			self.rotation = 315.1
			flag = True

		if flag:
			self.rotation_x = math.cos(coord.Coord.to_radians(-self.rotation))
			self.rotation_y = math.sin(coord.Coord.to_radians(-self.rotation))
			self.dx = self.__velocity * self.rotation_x 
			self.dy = self.__velocity * self.rotation_y
		
		# time_unit = dt
		if self.__fixed_time_quanta:
			time_quanta = 1.0/self.__fps
		else:
			time_quanta = dt
		self.x = self.x + self.dx * time_quanta
		self.y = self.y + self.dy * time_quanta

		current_position = self.get_current_coordinate()
		collided = self.__polygon_map.check_obstacle_collision(current_position) or self.__polygon_map.check_boundary_collision(current_position)
		if collided:
			self.revert_configuration()

		self.__update_visibility()
		# print('x,y:',self.x,self.y)


	def __update_visibility(self):
		self._visibility_polygon = self.__polygon_map.get_visibility_polygon(self.get_current_coordinate(), self.rotation, self._num_rays, self._visibility_angle)
		# print('Poly tuples:', self._visibility_polygon.get_points_tuple())
		self.__visibility_vertices.vertices = self._visibility_polygon.get_points_tuple()
		

class Graphics(pyglet.window.Window):

	def __init__(self, window_width, window_height, num_hiders, num_seekers, log_flag, replay_output_file, fps, velocity, polygon_map, fixed_time_quanta):
		super(Graphics, self).__init__(window_width, window_height)
		pyglet.resource.path.append('resources')
		pyglet.resource.reindex()
		self.__background = pyglet.graphics.OrderedGroup(0)
		self.__foreground = pyglet.graphics.OrderedGroup(1)
		self.__static_batch = pyglet.graphics.Batch()
		self.__dynamic_batch = pyglet.graphics.Batch()
		self.__hider_image = pyglet.resource.image('wanderer.png')
		self.__seeker_image = pyglet.resource.image('seeker.png')
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__fps_display = pyglet.clock.ClockDisplay()
		self.__log_flag = log_flag
		self.__replay_output_file = replay_output_file
		assert(isinstance(polygon_map, gamemap.PolygonMap))
		self.__polygon_map = polygon_map
		self.__polygons = [] # By polygons we refer to the background obstacles only


		self.__num_polygons = polygon_map.get_num_polygons()
		for i in range(self.__num_polygons):
			polygon = self.__polygon_map.get_polygon(i)
			self.__polygons.append(polygon)
			self.__add_batch_polygon(polygon)

		self.__boundary_polygon = polygon_map.get_boundary_polygon()
		self.__add_batch_polygon(self.__boundary_polygon)
			
		self.__hiders = [Player(self.__hider_image, self.__dynamic_batch, self.__background, self.__foreground, self.__polygon_map, window_width, window_height, 0, 0, 0, fps, velocity, fixed_time_quanta) for i in range(num_hiders)]
		self.__seekers = [Player(self.__seeker_image, self.__dynamic_batch, self.__background, self.__background, self.__polygon_map, window_width, window_height, 0, 0, 0, fps, velocity, fixed_time_quanta) for i in range(num_seekers)]
		
		self.__hider_active = [True for i in range(num_hiders)]
		self.__seeker_active = [True for i in range(num_seekers)]

		self.push_handlers(self.__seekers[0])

	def __add_batch_polygon(self, polygon):
		assert(polygon.get_num_vertices() == 4 or polygon.get_num_vertices() == 3)
		if polygon.get_num_vertices() == 4:
			self.__static_batch.add_indexed(4, pyglet.gl.GL_LINES, self.__background, 
			[0,1,1,2,2,3,3,0],
			('v2i', polygon.get_points_tuple()),)
		if polygon.get_num_vertices() == 3:
			self.__static_batch.add_indexed(3, pyglet.gl.GL_LINES, self.__background, 
			[0,1,1,2,2,0],
			('v2i', polygon.get_points_tuple() ),)

	def __type2player(self, player_type):
		if player_type == agent.AgentType.Hider:
			players = self.__hiders
		elif player_type == agent.AgentType.Seeker:
			players = self.__seekers
		return players

	def __type2player_active(self, player_type):
		if player_type == agent.AgentType.Hider:
			player_active = self.__hider_active
		elif player_type == agent.AgentType.Seeker:
			player_active = self.__seeker_active
		return player_active


	def set_player_inactive(self, player_type, player_idx):
		players = self.__type2player(player_type)
		player_active = self.__type2player_active(player_type)
		player_active[player_idx] = False
		players[player_idx].remove()
		players[player_idx] = None

	def set_player_action(self, player_type, player_idx, act):
		players = self.__type2player(player_type)
		players[player_idx].set_action(act)

	def get_player_percept(self, player_type, player_idx):
		players = self.__type2player(player_type)
		return players[player_idx].get_percept()

	def set_player_position(self, player_type, player_idx, position):
		players = self.__type2player(player_type)
		players[player_idx].set_position(position)

	def get_player_position(self, player_type, player_idx):
		players = self.__type2player(player_type)
		return players[player_idx].get_position()

	def set_player_position_raw(self, player_type, player_idx, x, y):
		players = self.__type2player(player_type)
		players[player_idx].set_position_raw(x, y)

	def set_player_rotation_raw(self, player_type, player_idx, rotation):
		players = self.__type2player(player_type)
		players[player_idx].set_rotation_raw(rotation)

	def set_player_visibility_polygon_raw(self, player_type, player_idx, points_tuple):
		players = self.__type2player(player_type)
		players[player_idx].set_visibility_polygon_raw(points_tuple)

	def on_draw(self):
		self.clear()
		self.__dynamic_batch.draw()
		self.__static_batch.draw()
		self.__fps_display.draw()

	def __get_visible_players(self, visibility_polygon, ignore_hiders, ignore_seekers):
		hider_coords = []
		hider_idxs = []
		for i in range(self.__num_hiders):
			if self.__hider_active[i]:
				if i in ignore_hiders:
					continue
				position = self.__hiders[i].get_current_coordinate()
				if visibility_polygon.is_point_inside(position):
					hider_coords.append(position)
					hider_idxs.append(i)

		seeker_coords = []
		seeker_idxs = []
		for i in range(self.__num_seekers):
			if self.__seeker_active[i]:
				if i in ignore_seekers:
					continue
				position = self.__seekers[i].get_current_coordinate()
				if visibility_polygon.is_point_inside(position):
					seeker_coords.append(position)
					seeker_idxs.append(i)

		return hider_coords, seeker_coords, hider_idxs, seeker_idxs

	def __update_percepts(self):
		'''
			Iterates over each players visibility region to check if any other 
			player is visible or not, preparing the percept accordingly.
		'''
		for i in range(self.__num_hiders):
			if self.__hider_active[i]:
				hider = self.__hiders[i]
				visibility_polygon = hider.get_visibility_polygon()
				ignore_hiders = [i]
				ignore_seekers = []
				hider_coords, seeker_coords, hider_idxs, seeker_idxs = self.__get_visible_players(visibility_polygon, ignore_hiders, ignore_seekers)
				# if hider_coords:
				# 	print('Hider spotted:', hider_coords)
				# if seeker_coords:
				# 	print('Seeker spotted:', seeker_coords)
				current_percept = percept.GraphicsPercept(hider_coords, seeker_coords, hider_idxs, seeker_idxs)
				hider.set_percept(current_percept)

		for i in range(self.__num_seekers):
			if self.__seeker_active[i]:
				seeker = self.__seekers[i]
				visibility_polygon = seeker.get_visibility_polygon()
				ignore_hiders = []
				ignore_seekers = [i]
				hider_coords, seeker_coords, hider_idxs, seeker_idxs = self.__get_visible_players(visibility_polygon, ignore_hiders, ignore_seekers)
				# if hider_coords:
				# 	print('Hider spotted:', hider_coords)
				# if seeker_coords:
				# 	print('Seeker spotted:', seeker_coords)
				current_percept = percept.GraphicsPercept(hider_coords, seeker_coords, hider_idxs, seeker_idxs)
				seeker.set_percept(current_percept)

	def update(self, dt):
		occupied_positions = []
		hiders_pos_string = ''
		for i in range(self.__num_hiders):
			if self.__hider_active[i]:
				self.__hiders[i].update(dt)
				current_position = self.__hiders[i].get_current_coordinate()
				collided = self.__polygon_map.check_obstacle_collision(current_position) or self.__polygon_map.check_boundary_collision(current_position)
				obstructed = current_position in occupied_positions

				if collided or obstructed:
					 self.__hiders[i].revert_configuration()
				else:
					occupied_positions.append(current_position)

				if self.__log_flag:
					x = self.__hiders[i].get_current_coordinate().get_x()
					y = self.__hiders[i].get_current_coordinate().get_y()
					act = self.__hiders[i].get_action()
					if i != 0:
						hiders_pos_string += '; '
					hiders_pos_string += str(x) + ',' + str(y) + ',' + action.Action.action2string[act]
					points_string = str(self.__hiders[i].get_visibility_polygon().get_points_tuple())[1:-1]
					hiders_pos_string += '*' + points_string
			else:
				if self.__log_flag:
					if i != 0:
						hiders_pos_string += '; '
					hiders_pos_string += 'X*X'
		# print(hiders_pos_string)

		seekers_pos_string = ''
		for i in range(self.__num_seekers):
			if self.__seeker_active[i]:
				self.__seekers[i].update(dt)
				current_position = self.__seekers[i].get_current_coordinate()
				collided = self.__polygon_map.check_obstacle_collision(current_position) or self.__polygon_map.check_boundary_collision(current_position)
				obstructed = current_position in occupied_positions
				if collided or obstructed:
					 self.__seekers[i].revert_configuration()
				else:
					occupied_positions.append(current_position)

				if self.__log_flag:
					x = self.__seekers[i].get_current_coordinate().get_x()
					y = self.__seekers[i].get_current_coordinate().get_y()
					act = self.__seekers[i].get_action()
					if i != 0:
						seekers_pos_string += '; '
					seekers_pos_string += str(x) + ',' + str(y) + ',' + action.Action.action2string[act]
					points_string = str(self.__seekers[i].get_visibility_polygon().get_points_tuple())[1:-1]
					seekers_pos_string += '*' + points_string

			else:
				if self.__log_flag:
					if i != 0:
						seekers_pos_string += '; '
					seekers_pos_string += 'X*X'
		# print(seekers_pos_string)
		if self.__log_flag:
			self.__replay_output_file.write(hiders_pos_string+'\n')
			self.__replay_output_file.write(seekers_pos_string+'\n')

		self.__update_percepts()
