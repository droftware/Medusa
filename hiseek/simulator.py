import random
import copy

import pyglet

import statistic
import gamemap
import team
import percept
import action
import graphics

class Simulator(object):
	"""
		Responsible for one complete simulation
	"""

	mode_type_hiders = ['random']
	mode_type_seekers = ['random']

	def __init__(self, display, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, verbose, max_steps=1000, window_width=640, window_height=360):
		self.__display = display
		assert(mode_hiders in Simulator.mode_type_hiders)
		assert(mode_seekers in Simulator.mode_type_seekers)
		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file
		self.__verbose = verbose
		self.__stats = statistic.Statistic(num_hiders, num_seekers)
		self.__max_steps = max_steps
		self.__fps = 1/60.
		self.__map = gamemap.PolygonMap(0)

		hider_map_copy = copy.deepcopy(self.__map)
		seeker_map_copy = copy.deepcopy(self.__map)

		# AI setup
		if mode_hiders == 'random':
			self.__hider_team = team.RandomHiderTeam(num_hiders, hider_map_copy)
		if mode_seekers == 'random':
			self.__seeker_team = team.RandomSeekerTeam(num_seekers, seeker_map_copy)

		# Graphics setup
		self.__window_width = self.__map.get_map_width()
		self.__window_height = self.__map.get_map_height()
		self.__window = graphics.Graphics(self.__window_width, self.__window_height, num_hiders, num_seekers, self.__map)
		
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
		self.__caught = [[False for j in range(self.__hider_team.get_num_rankers(i))] for i in range(self.__hider_team.get_ranks())]
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
			if not self.__caught[rank][idx]:
				current_percept = self.__window.get_hider_percept(i)
				# print(current_percept)
				converted_percept = self.__graphics2team_percept(current_percept)
				self.__hider_team.set_percept(rank, idx, converted_percept)

	def __transfer_seeker_percepts(self):
		for i in range(self.__num_seekers):
			rank, idx = self.__seekers_player2agent[i]
			current_percept = self.__window.get_seeker_percept(i)
			# print(current_percept)
			converted_percept = self.__graphics2team_percept(current_percept)
			self.__seeker_team.set_percept(rank, idx, converted_percept)

	def __transfer_hider_actions(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				if not self.__caught[rank][ai_idx]:
					graphics_idx = self.__hiders_agent2player[(rank, ai_idx)]
					act = self.__hider_team.get_action(rank, ai_idx)
					self.__window.set_hider_action(graphics_idx, act)

	def __transfer_seeker_actions(self):
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__seekers_agent2player[(rank, ai_idx)]
				act = self.__seeker_team.get_action(rank, ai_idx)
				self.__window.set_seeker_action(graphics_idx, act)

	def __set_hider_openings(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__hiders_agent2player[(rank, ai_idx)]
				position = self.__hider_team.get_position(rank, ai_idx)
				self.__window.set_hider_position(graphics_idx ,position)

	def __set_seeker_openings(self):
		for i in range(self.__seeker_team.get_ranks()):
			for j in range(self.__seeker_team.get_num_rankers(i)):
				rank, ai_idx = i, j
				graphics_idx = self.__seekers_agent2player[(rank, ai_idx)]
				position = self.__seeker_team.get_position(rank, ai_idx)
				self.__window.set_seeker_position(graphics_idx, position)

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
			print(self.__num_caught,':Hider caught:', rank, ai_idx)
			if not self.__caught[rank][ai_idx]:
				self.__caught[rank][ai_idx] = True
				self.__hider_team.set_member_inactive(rank, ai_idx)
				self.__window.set_hider_inactive(graphics_idx)
				self.__num_caught += 1


	def __update_simulation(self, dt):
		# update the time
		# print('dt:', dt)
		self.__total_time += dt

		# extract percept from graphics layer and send to ai layer
		self.__transfer_hider_percepts()
		self.__transfer_seeker_percepts()

		# check if any hider is caught by a seeker and inform the AI layer
		self.__check_hider_caught()

		# update the states in ai layer so that they selct actions
		self.__hider_team.select_actions()
		self.__seeker_team.select_actions()

		# extract actions from ai layer and send it to graphics layer
		self.__transfer_hider_actions()
		self.__transfer_seeker_actions()
			
		# Update the game window
		self.__window.update(dt)

		if self.__num_caught == self.__num_hiders:
			print('All hiders caught')
			print('Total time take:', self.__total_time)
			print('Total steps taken:', self.__total_time * (1/self.__fps))
			pyglet.app.exit()

	def simulate(self):
		# pyglet.gl.glClearColor(255,255,255,0)
		self.__set_hider_openings()
		self.__set_seeker_openings()
		pyglet.clock.schedule_interval(self.__update_simulation, self.__fps)
		pyglet.app.run()
		