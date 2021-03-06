import random
import copy
import math

import pyglet

import statistic
import gamemap
import team
import percept
import action
import graphics
import agent
import coord

class Mover(object):
	def __init__(self, polygon_map, pos_x, pos_y, pos_rot, fps, velocity, fixed_time_quanta, num_rays, visibility_angle):
		self.__x = pos_x
		self.__y = pos_y
		self.__rotation = pos_rot
		self.__dx = 0
		self.__dy = 0
		self.__rotation_x = 0
		self.__rotation_y = 0
		self.__action = None
		self.__motion = None

		self.__current_percept = percept.GraphicsPercept([],[],[],[])

		self.__polygon_map = polygon_map
		self.__num_rays = num_rays
		self.__visibility_angle = visibility_angle
		self.__visibility_polygon = None

		self.__fps = fps
		self.__velocity = velocity
		self.__fixed_time_quanta = fixed_time_quanta

	def get_current_coordinate(self):
		return coord.Coord(self.__x, self.__y)

	def get_rotation(self):
		return self.__rotation

	def set_action(self, act):
		assert(act, action.Action)
		self.__action = act

	def set_motion(self, motion):
		# assert(motion, action.Action)
		self.__motion = motion

	def get_action(self):
		return self.__action

	def set_percept(self, current_percept):
		self.__current_percept = current_percept

	def get_percept(self):
		return self.__current_percept

	def revert_configuration(self):
		self.__x = self.__prev_x
		self.__y = self.__prev_y
		self.__rotation = self.__prev_rotation
		self.__update_visibility()

	def set_visibility(self, visibility):
		self.visible = visibility

	def set_position(self, position):
		self.__x = position.get_x()
		self.__y = position.get_y()

	def get_visibility_polygon(self):
		return self.__visibility_polygon

	def __update_visibility(self):
		self.__visibility_polygon = self.__polygon_map.get_visibility_polygon(self.get_current_coordinate(), self.__rotation, self.__num_rays, self.__visibility_angle)
		# print('Poly tuples:', self.__visibility_polygon.get_points_tuple())
		# self.__visibility_vertices.vertices = self.__visibility_polygon.get_points_tuple()

	def update(self, dt):
		self.__dx = 0
		self.__dy = 0

		flag = False

		self.__prev_x = self.__x
		self.__prev_y = self.__y
		self.__prev_rotation = self.__rotation

		if self.__action != action.Action.ST:
			self.__rotation = action.ROTATION[self.__action]
			flag = True
		# print('update rotation:', self.__rotation)
		if flag:
			self.__rotation_x = math.cos(coord.Coord.to_radians(-self.__rotation))
			self.__rotation_y = math.sin(coord.Coord.to_radians(-self.__rotation))
			self.__dx = self.__velocity * self.__rotation_x 
			self.__dy = self.__velocity * self.__rotation_y

		# time_unit = dt
		if self.__fixed_time_quanta:
			time_quanta = 1.0/self.__fps
		else:
			time_quanta = dt

		if self.__motion:
			self.__x = self.__x + self.__dx * time_quanta
			self.__y = self.__y + self.__dy * time_quanta

		current_position = self.get_current_coordinate()
		collided = self.__polygon_map.check_obstacle_collision(current_position) or self.__polygon_map.check_boundary_collision(current_position)
		if collided:
			self.revert_configuration()

		self.__update_visibility()
		# print('x,y:',self.__x,self.__y)

class Simulator(object):
	"""
		Responsible for one complete simulation
	"""

	mode_type_hiders = ['random', 'bayesian', 'sbandit', 'hm_sbandit', 'hv_sbandit', 'hmv_sbandit', 'human', 'offset']
	mode_type_seekers = ['random', 'sbandit', 'coverage', 'cc', 'human', 'wave', 'trap']

	def __init__(self, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, conf_options, log_flag, vis_flag, total_step_times, sim_turn, max_steps=1000, window_width=640, window_height=360):
		assert(mode_hiders in Simulator.mode_type_hiders)
		assert(mode_seekers in Simulator.mode_type_seekers)

		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file

		self.__conf_options = conf_options
		self.__fps = self.__conf_options.get_fps()
		self.__velocity = self.__conf_options.get_velocity()
		self.__fixed_time_quanta = self.__conf_options.get_fixed_time_quanta()
		self.__verbose = self.__conf_options.get_verbose()
		self.__num_rays = self.__conf_options.get_num_rays()
		self.__visibility_angle = self.__conf_options.get_visibility_angle()
		self.__show_fellows = self.__conf_options.get_show_fellows()
		self.__show_opponent = self.__conf_options.get_show_opponent()

		self.__sim_turn = sim_turn
		self.__stats = statistic.Statistic(num_hiders, num_seekers, self.__map_id, self.__sim_turn)
		self.__max_steps = max_steps
		self.__steps = 0
		self.__polygon_map = gamemap.PolygonMap(map_id)

		self.__log_flag = log_flag
		self.__vis_flag = vis_flag
		self.__replay_output_file = None

		self._total_step_times = total_step_times


		if log_flag:
			print('Logging initiated:', output_file)
			self.__replay_output_file = open(output_file, 'w')
			self.__replay_output_file.write('map_id:' + str(map_id) + '\n')
			self.__replay_output_file.write('num_hiders:' + str(num_hiders) + '\n')
			self.__replay_output_file.write('num_seekers:' +  str(num_seekers) + '\n')
			self.__replay_output_file.write('simulation:' + '\n')

		hider_map_copy = gamemap.PolygonMap(map_id)
		seeker_map_copy = gamemap.PolygonMap(map_id)

		# AI setup
		if mode_hiders == 'random':
			self.__hider_team = team.RandomTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)
		elif mode_hiders == 'bayesian':
			self.__hider_team = team.BayesianTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)
		elif mode_hiders == 'sbandit':
			self.__hider_team = team.UCBPassiveTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle, False, False)
		elif mode_hiders == 'hm_sbandit':
			self.__hider_team = team.UCBPassiveTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle, True, False)
		elif mode_hiders == 'hv_sbandit':
			self.__hider_team = team.UCBPassiveTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle, False, True)
		elif mode_hiders == 'hmv_sbandit':
			self.__hider_team = team.UCBPassiveTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle, True, True)
		elif mode_hiders == 'human':
			self.__hider_team = team.HumanRandomTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)
		elif mode_hiders == 'offset':
			self.__hider_team = team.OffsetTeam(agent.AgentType.Hider, num_hiders, hider_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)

		if mode_seekers == 'random':
			self.__seeker_team = team.RandomTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)
		elif mode_seekers == 'sbandit':
			self.__seeker_team = team.UCBAggressiveTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle)
		elif mode_seekers == 'coverage':
			self.__seeker_team = team.UCBCoverageTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle)
		elif mode_seekers == 'cc':
			self.__seeker_team = team.UCBCoverageCommunicationTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle)
		elif mode_seekers == 'human':
			self.__seeker_team = team.HumanRandomTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta)
		elif mode_seekers == 'wave':
			self.__seeker_team = team.WaveTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle)
		elif mode_seekers == 'trap':
			self.__seeker_team = team.TrapTeam(agent.AgentType.Seeker, num_seekers, seeker_map_copy, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle)

		# Graphics setup
		self.__window_width = self.__polygon_map.get_map_width()
		self.__window_height = self.__polygon_map.get_map_height()
		self.__texture_flag = self.__conf_options.get_texture_flag()
		dynamic_batching_flag = True
		show_hiders_flag = True
		show_seekers_flag = True
		if mode_hiders == 'human':
			dynamic_batching_flag = False
			show_seekers_flag = self.__show_opponent
		if mode_seekers == 'human':
			dynamic_batching_flag = False
			show_hiders_flag = self.__show_opponent
		if self.__vis_flag:
			self.__window = graphics.Graphics(self.__window_width, self.__window_height, num_hiders, num_seekers, self.__polygon_map, self.__conf_options, dynamic_batching_flag, show_hiders_flag, show_seekers_flag, self.__texture_flag)
		else:
			self.__window = None

		# Movers setup
		self.__hiders = [Mover(self.__polygon_map, 0, 0, 0, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle) for i in range(num_hiders)]
		self.__seekers = [Mover(self.__polygon_map, 0, 0, 0, self.__fps, self.__velocity, self.__fixed_time_quanta, self.__num_rays, self.__visibility_angle) for i in range(num_seekers)]

		# Mover active list
		self.__hiders_active = [True for i in range(num_hiders)]
		self.__seekers_active = [True for i in range(num_seekers)]


		# Mapping AI agents and Graphics players for interchange of percepts and 
		# actions
		self.__hiders_agent2player = {}
		self.__hiders_player2agent = [None for i in range(self.__num_hiders)]
		counter = 0
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = counter
				self.__hiders_agent2player[(rank, ai_idx)] = graphics_idx
				self.__hiders_player2agent[graphics_idx] = (rank, ai_idx)
				counter += 1

		self.__seekers_agent2player ={}
		self.__seekers_player2agent = [None for i in range(self.__num_seekers)]
		counter = 0
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = counter
				self.__seekers_agent2player[(rank, ai_idx)] = graphics_idx
				self.__seekers_player2agent[graphics_idx] = (rank, ai_idx)
				counter += 1

		# Initializing the caught list by setting all hiders as NOT CAUGHT
		# self.__caught = [[False for j in range(self.__hider_team.get_num_rankers(i))] for i in range(self.__hider_team.get_ranks())]
		self.__num_caught = 0
		self.__total_time = 0

	def __graphics2team_percept(self, current_percept):
		assert(current_percept, percept.GraphicsPercept)
		hider_coords = current_percept.get_hiders()
		hider_idxs = current_percept.get_hider_idxs()
		hider_uids = []
		for i in range(len(hider_idxs)):
			uid = self.__hiders_player2agent[hider_idxs[i]]
			hider_uids.append(uid)

		seeker_coords = current_percept.get_seekers()
		seeker_idxs = current_percept.get_seeker_idxs()
		seeker_uids = []
		for i in range(len(seeker_idxs)):
			uid = self.__seekers_player2agent[seeker_idxs[i]]
			seeker_uids.append(uid)

		converted_percept = percept.TeamPercept(hider_coords, seeker_coords, hider_uids, seeker_uids)
		return converted_percept

	def __transfer_hider_percepts(self):
		for i in range(self.__num_hiders):
			rank, idx = self.__hiders_player2agent[i]
			# if not self.__caught[rank][idx]:
			if self.__hiders_active[i]:
				current_percept = self.__hiders[i].get_percept()
				converted_percept = self.__graphics2team_percept(current_percept)
				self.__hider_team.set_percept(rank, idx, converted_percept)

	def __transfer_seeker_percepts(self):
		for i in range(self.__num_seekers):
			rank, idx = self.__seekers_player2agent[i]
			current_percept = self.__seekers[i].get_percept()
			converted_percept = self.__graphics2team_percept(current_percept)
			self.__seeker_team.set_percept(rank, idx, converted_percept)

	def __transfer_hider_positions(self):
		for i in range(self.__num_hiders):
			rank, idx = self.__hiders_player2agent[i]
			# if not self.__caught[rank][idx]:
			if self.__hiders_active[i]:
				current_position = self.__hiders[i].get_current_coordinate()
				self.__hider_team.set_position(rank, idx, current_position)

	def __transfer_seeker_positions(self):
		for i in range(self.__num_seekers):
			rank, idx = self.__seekers_player2agent[i]
			current_position = self.__seekers[i].get_current_coordinate()
			self.__seeker_team.set_position(rank, idx, current_position)

	def __transfer_hider_actions(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__hiders_agent2player[(rank, ai_idx)]
				# if not self.__caught[rank][ai_idx]:
				if self.__hiders_active[graphics_idx]:
					act = self.__hider_team.get_action(rank, ai_idx)
					self.__hiders[graphics_idx].set_action(act)

	def __transfer_seeker_actions(self):
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__seekers_agent2player[(rank, ai_idx)]
				act = self.__seeker_team.get_action(rank, ai_idx)
				self.__seekers[graphics_idx].set_action(act)

	def __transfer_hider_motions(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__hiders_agent2player[(rank, ai_idx)]
				# if not self.__caught[rank][ai_idx]:
				if self.__hiders_active[graphics_idx]:
					motion = self.__hider_team.get_motion(rank, ai_idx)
					self.__hiders[graphics_idx].set_motion(motion)

	def __transfer_seeker_motions(self):
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__seekers_agent2player[(rank, ai_idx)]
				motion = self.__seeker_team.get_motion(rank, ai_idx)
				self.__seekers[graphics_idx].set_motion(motion)

	def __set_hider_openings(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__hiders_agent2player[(rank, ai_idx)]
				position = self.__hider_team.get_position(rank, ai_idx)
				self.__hiders[graphics_idx].set_position(position)

	def __set_seeker_openings(self):
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__seekers_agent2player[(rank, ai_idx)]
				position = self.__seeker_team.get_position(rank, ai_idx)
				self.__seekers[graphics_idx].set_position(position)

	def __type2mover(self, mover_type):
		if mover_type == agent.AgentType.Hider:
			movers = self.__hiders
		elif mover_type == agent.AgentType.Seeker:
			movers = self.__seekers
		return movers

	def __type2mover_active(self, mover_type):
		if mover_type == agent.AgentType.Hider:
			mover_active = self.__hiders_active
		elif mover_type == agent.AgentType.Seeker:
			mover_active = self.__seekers_active
		return mover_active

	def __set_mover_inactive(self, mover_type, mover_idx):
		movers = self.__type2mover(mover_type)
		mover_active = self.__type2mover_active(mover_type)
		mover_active[mover_idx] = False
		# movers[mover_idx].remove()
		movers[mover_idx] = None
		if self.__vis_flag:
			self.__window.set_player_inactive(mover_type, mover_idx)


	def __check_hider_caught(self):
		visible_hiders = []
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				current_percept = self.__seeker_team.get_percept(rank, ai_idx)
				if current_percept.are_hiders_visible():
					visible_hiders = visible_hiders + current_percept.get_hider_uids()

		for i in range(len(visible_hiders)):
			rank, ai_idx = visible_hiders[i]
			graphics_idx = self.__hiders_agent2player[visible_hiders[i]]
			# print('')
			# print(self.__num_caught,':Hider caught:', graphics_idx)
			if self.__hiders_active[graphics_idx]:
				self.__hiders_active[graphics_idx] = False 
				self.__hider_team.set_member_inactive(rank, ai_idx)
				self.__set_mover_inactive(agent.AgentType.Hider, graphics_idx)
				self.__num_caught += 1
				print('Hider caught !!, total:{}'.format(self.__num_caught))


				# Updating the statistics
				self.__stats.update_hider_caught_time(graphics_idx, self.__steps)


	def __get_visible_players(self, visibility_polygon, ignore_hiders, ignore_seekers):
		hider_coords = []
		hider_idxs = []
		for i in range(self.__num_hiders):
			if self.__hiders_active[i]:
				if i in ignore_hiders:
					continue
				position = self.__hiders[i].get_current_coordinate()
				if visibility_polygon.is_point_inside(position):
					hider_coords.append(position)
					hider_idxs.append(i)

		seeker_coords = []
		seeker_idxs = []
		for i in range(self.__num_seekers):
			if self.__seekers_active[i]:
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
			if self.__hiders_active[i]:
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
			if self.__seekers_active[i]:
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


	def __update_game(self, dt):
		occupied_positions = []
		hiders_pos_string = ''
		for i in range(self.__num_hiders):
			if self.__hiders_active[i]:
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

					# Updating the statistics
					self.__stats.update_hider_path(i, self.__hiders[i].get_current_coordinate())

			else:
				if self.__log_flag:
					if i != 0:
						hiders_pos_string += '; '
					hiders_pos_string += 'X*X'
		# print(hiders_pos_string)

		seekers_pos_string = ''
		for i in range(self.__num_seekers):
			if self.__seekers_active[i]:
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

					# Updating the statistics
					self.__stats.update_seeker_path(i, self.__seekers[i].get_current_coordinate())


			else:
				if self.__log_flag:
					if i != 0:
						seekers_pos_string += '; '
					seekers_pos_string += 'X*X'
		# print(seekers_pos_string)
		if self.__log_flag:
			self.__replay_output_file.write(hiders_pos_string+'\n')
			self.__replay_output_file.write(seekers_pos_string+'\n')

	def __update_mover_graphics_configuration(self, mover_type, mover_idx):
		movers = self.__type2mover(mover_type)
		current_position = movers[mover_idx].get_current_coordinate()
		x = current_position.get_x()
		y = current_position.get_y()
		# print('Setting position:', str(current_position))
		rotn = movers[mover_idx].get_rotation()
		self.__window.set_player_position_raw(mover_type, mover_idx, x, y)
		self.__window.set_player_rotation_raw(mover_type, mover_idx, rotn)

	def __update_mover_graphics_visibility(self, mover_type, mover_idx):
		movers = self.__type2mover(mover_type)
		visibility_tuple = movers[mover_idx].get_visibility_polygon().get_points_tuple()
		self.__window.set_player_visibility_polygon_raw(mover_type, mover_idx, visibility_tuple)

	def __update_graphics_configuration(self):
		for i in range(self.__num_hiders):
			if self.__hiders_active[i]:
				# print('Updating hider:', i)
				self.__update_mover_graphics_configuration(agent.AgentType.Hider, i)
		for i in range(self.__num_seekers):
			if self.__seekers_active[i]:
				# print('Updating seeker:', i)
				self.__update_mover_graphics_configuration(agent.AgentType.Seeker, i)

	def __update_graphics_visibility(self):
		for i in range(self.__num_hiders):
			if self.__hiders_active[i]:
				self.__update_mover_graphics_visibility(agent.AgentType.Hider, i)
		for i in range(self.__num_seekers):
			if self.__seekers_active[i]:
				self.__update_mover_graphics_visibility(agent.AgentType.Seeker, i)

	def __handle_hider_keys(self):
		if self.__mode_hiders == 'human':
			key = self.__window.get_key()
			if key == 'SPACE':
				self.__hider_team.toggle_human_player()
			else:
				self.__hider_team.set_key(self.__window.get_key())

	def __handle_seeker_keys(self):
		if self.__mode_seekers == 'human':
			key = self.__window.get_key()
			if key == 'SPACE':
				self.__seeker_team.toggle_human_player()
			else:
				self.__seeker_team.set_key(self.__window.get_key())	


	def __enable_seeker_show(self):
		if self.__mode_seekers == 'human':

			if self.__show_opponent:
				self.__window.set_show_players(agent.AgentType.Hider, True)
			else:
				self.__window.set_show_players(agent.AgentType.Hider, False)


			seeker_ids_list = None
			if self.__show_fellows:
				seeker_ids_list = range(self.__num_seekers)
				self.__window.set_show_players(agent.AgentType.Seeker, True)
			else:
				self.__window.set_show_players(agent.AgentType.Seeker, False)
				human_agent_id = self.__seeker_team.get_human_agent_id()
				human_player_id = self.__seekers_agent2player[human_agent_id]
				seeker_ids_list = [human_player_id]
				self.__window.set_show_player(agent.AgentType.Seeker, human_player_id, True)

			for seeker_id in seeker_ids_list:
				if self.__seekers_active[seeker_id]:
					seeker = self.__seekers[seeker_id]
					current_percept = seeker.get_percept()
					visible_hider_ids = current_percept.get_hider_idxs()
					visible_seeker_ids = current_percept.get_seeker_idxs()
					for i in visible_hider_ids:
						self.__window.set_show_player(agent.AgentType.Hider, i, True)				

					for i in visible_seeker_ids:
						self.__window.set_show_player(agent.AgentType.Seeker, i, True)

	def __enable_hider_show(self):
		if self.__mode_hiders == 'human':

			if self.__show_opponent:
				self.__window.set_show_players(agent.AgentType.Seeker, True)
			else:
				self.__window.set_show_players(agent.AgentType.Seeker, False)

			hider_ids_list = None
			if self.__show_fellows:
				hider_ids_list = range(self.__num_hiders)
				self.__window.set_show_players(agent.AgentType.Hider, True)
			else:
				self.__window.set_show_players(agent.AgentType.Hider, False)
				human_agent_id = self.__hider_team.get_human_agent_id()
				human_player_id = self.__hiders_agent2player[human_agent_id]
				hider_ids_list = [human_player_id]
				self.__window.set_show_player(agent.AgentType.Hider, human_player_id, True)

			for hider_id in hider_ids_list:
				if self.__hiders_active[hider_id]:
					hider = self.__hiders[hider_id]
					current_percept = hider.get_percept()
					visible_hider_ids = current_percept.get_hider_idxs()
					visible_seeker_ids = current_percept.get_seeker_idxs()
					for i in visible_hider_ids:
						self.__window.set_show_player(agent.AgentType.Hider, i, True)				

					for i in visible_seeker_ids:
						self.__window.set_show_player(agent.AgentType.Seeker, i, True)


	def __update_simulation(self, dt):
		# update the time
		# print('dt:', dt)
		self.__total_time += dt
		self.__steps += 1
		
		# extract percept from simulation layer and send to AI layer
		self.__transfer_hider_percepts()
		self.__transfer_seeker_percepts()

		# extract positions from simulation layer and send to AI layer
		self.__transfer_hider_positions()
		self.__transfer_seeker_positions()

		# check if any hider is caught by a seeker and inform the AI layer
		self.__check_hider_caught()

		# If a human player is involved, pass the key pressed to AI layer
		self.__handle_hider_keys()
		self.__handle_seeker_keys()
		
		# update the states in ai layer so that they select actions
		self.__hider_team.select_actions()
		self.__seeker_team.select_actions()

		# update the states in ai layer so that they select wether they want 
		# to move or not
		self.__hider_team.select_motions()
		self.__seeker_team.select_motions()

		# extract actions from ai layer and send it to simulation layer
		self.__transfer_hider_actions()
		self.__transfer_seeker_actions()

		# extract actions from ai layer and send it to simulation layer
		self.__transfer_hider_motions()
		self.__transfer_seeker_motions()
			
		# Update the position of players after incorporating the actions obtained
		self.__update_game(dt)

		# Update the percepts obtained after incorporating the new position
		self.__update_percepts()

		# If a human player is involved, handle selective show of players
		self.__enable_seeker_show()
		self.__enable_hider_show()

		# If visibility flag is enabled, update the graphics
		if self.__vis_flag:
			self.__update_graphics_configuration()
			self.__update_graphics_visibility()

		if self.__num_caught == self.__num_hiders:
			print('Total steps:', self.__steps)
			print('All hiders caught')
			self._total_step_times.append(self.__steps)
			# self.__stats.print_statistic()
			self.__stats.write_statistic()
			if self.__log_flag:
				print()
				print('## Closing log file')
				self.__replay_output_file.close()
			if self.__vis_flag:
				pyglet.app.exit()
			return False
		else:
			return True

	def simulate(self):
		# pyglet.gl.glClearColor(255,255,255,0)
		self.__set_hider_openings()
		self.__set_seeker_openings()
		if self.__vis_flag:
			self.__update_graphics_configuration()
		if self.__vis_flag:
			pyglet.clock.schedule_interval(self.__update_simulation, 1/self.__fps)
			pyglet.app.run()
		else:
			while(True):
				if not self.__update_simulation(1/self.__fps):
					break

		