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

class Player(pyglet.sprite.Sprite):

	def __init__(self, img, batch, background, foreground, polygon_map, pos_x, pos_y, pos_rot, num_rays):
		super(Player, self).__init__(img, pos_x, pos_y, batch=batch, group=foreground)
		Player.center_anchor(img)
		self.scale = 0.6
		self.rotation = pos_rot
		self.dx = 0
		self.dy = 0
		
		self.__prev_x = None
		self.__prev_y = None
		self.__prev_rotation = None

		# Visibility polygon setup
		self._num_rays = num_rays
		self._visibility_color = 28, 40, 51
		# self._visibility_color = 132, 132, 132  

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
		for i in range(self._num_vertices):
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

	def set_position_raw(self, x, y):
		# print('Position set to :', x, y)
		# print('')
		self.x = x
		self.y = y

	def set_rotation_raw(self, rotation):
		self.rotation = rotation

	def set_visibility_polygon_raw(self, points_tuple):
		self.__visibility_vertices.vertices = points_tuple
		

class Graphics(pyglet.window.Window):

	def __init__(self, window_width, window_height, num_hiders, num_seekers, polygon_map, conf_options):
		super(Graphics, self).__init__(window_width, window_height, caption='Hiseek: Hide and Seek simulation')
		pyglet.resource.path.append('resources')
		pyglet.resource.reindex()
		self.__background = pyglet.graphics.OrderedGroup(0)
		self.__foreground = pyglet.graphics.OrderedGroup(1)
		self.__static_batch = pyglet.graphics.Batch()
		self.__dynamic_batch = pyglet.graphics.Batch()
		self.__hider_image = pyglet.resource.image(conf_options.get_hider_image())
		self.__seeker_image = pyglet.resource.image(conf_options.get_seeker_image())
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__fps_display = pyglet.clock.ClockDisplay()
		assert(isinstance(polygon_map, gamemap.PolygonMap))
		self.__polygon_map = polygon_map
		self.__polygons = [] # By polygons we refer to the background obstacles only
		self.__num_rays = conf_options.get_num_rays()
		self.__save_frame = conf_options.get_save_frame()
		self.__frame_count = 0
		self.__key = 'NONE'


		self.__num_polygons = polygon_map.get_num_polygons()
		for i in range(self.__num_polygons):
			polygon = self.__polygon_map.get_polygon(i)
			self.__polygons.append(polygon)
			self.__add_batch_polygon(polygon, True)

		self.__boundary_polygon = polygon_map.get_boundary_polygon()
		self.__add_batch_polygon(self.__boundary_polygon, False)
			
		self.__hiders = [Player(self.__hider_image, self.__dynamic_batch, self.__background, self.__foreground, self.__polygon_map, 0, 0, 0, self.__num_rays) for i in range(num_hiders)]
		self.__seekers = [Player(self.__seeker_image, self.__dynamic_batch, self.__background, self.__background, self.__polygon_map, 0, 0, 0, self.__num_rays) for i in range(num_seekers)]
		
		self.__hider_active = [True for i in range(num_hiders)]
		self.__seeker_active = [True for i in range(num_seekers)]

		self.push_handlers(self.__seekers[0])

	def __add_batch_polygon(self, polygon, is_filled):
		assert(polygon.get_num_vertices() == 4 or polygon.get_num_vertices() == 3)
		if is_filled:
			polygon_color = 74, 35, 90 
			# polygon_color = 20, 20, 20
			color_list = []
			for i in range(4):
				# 149, 165, 166
				color_list.append(polygon_color[0])
				color_list.append(polygon_color[1])
				color_list.append(polygon_color[2])
			color_tuple = tuple(color_list)
			if polygon.get_num_vertices() == 4:
				self.__static_batch.add_indexed(4, pyglet.gl.GL_TRIANGLES, self.__background, 
				[0,1,2,2,3,0],
				('v2i', polygon.get_points_tuple()),
				('c3B', color_tuple)
				)
		elif not is_filled:
			if polygon.get_num_vertices() == 4:
				self.__static_batch.add_indexed(4, pyglet.gl.GL_LINES, self.__background, 
				[0,1,1,2,2,3,3,0],
				('v2i', polygon.get_points_tuple()),)
		# if polygon.get_num_vertices() == 3:
		# 	self.__static_batch.add_indexed(3, pyglet.gl.GL_LINES, self.__background, 
		# 	[0,1,1,2,2,0],
		# 	('v2i', polygon.get_points_tuple() ),)

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

	def set_player_position_raw(self, player_type, player_idx, x, y):
		players = self.__type2player(player_type)
		# print('Player type:', player_type)
		# print('Player index:', player_idx)
		players[player_idx].set_position_raw(x, y)

	def set_player_rotation_raw(self, player_type, player_idx, rotation):
		players = self.__type2player(player_type)
		players[player_idx].set_rotation_raw(rotation)

	def set_player_visibility_polygon_raw(self, player_type, player_idx, points_tuple):
		players = self.__type2player(player_type)
		players[player_idx].set_visibility_polygon_raw(points_tuple)

	def on_draw(self):
		# pyglet.gl.glClearColor(1,1,1,1)
		self.clear()
		self.__dynamic_batch.draw()
		self.__static_batch.draw()
		if self.__save_frame:
			pyglet.image.get_buffer_manager().get_color_buffer().save('./frames/'+str(self.__frame_count)+'.png')
			self.__frame_count += 1
		self.__fps_display.draw()

	def on_key_press(self, symbol, modifiers):
		if symbol == key.LEFT:
			self.__key = 'LEFT'
		elif symbol == key.RIGHT:
			self.__key = 'RIGHT'
		elif symbol == key.UP:
			self.__key = 'UP'
		elif symbol == key.DOWN:
			self.__key = 'DOWN'

	def on_key_release(self, symbol, modifiers):
		self.__key = 'NONE'

	def get_key(self):
		return self.__key