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
		self.__map = gamemap.PolygonMap(0)

		hider_map_copy = copy.deepcopy(self.__map)
		seeker_map_copy = copy.deepcopy(self.__map)

		# AI setup
		if mode_hiders == 'random':
			self.__hider_team = team.RandomHiderTeam(num_hiders, self.__map)
		if mode_seekers == 'random':
			self.__seeker_team = team.RandomSeekerTeam(num_seekers, self.__map)

		# Graphics setup
		self.__window_width = window_width
		self.__window_height = window_height
		self.__window = graphics.Graphics(window_width, window_height, num_hiders, num_seekers, self.__map)
		
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

	def __transfer_hider_percepts(self):
		for i in range(self.__num_hiders):
			current_percept = self.__window.get_hider_percept(i)
			rank, idx = self.__hiders_player2agent[i]
			self.__hider_team.set_percept(rank, idx, current_percept)

	def __transfer_seeker_percepts(self):
		for i in range(self.__num_seekers):
			current_percept = self.__window.get_seeker_percept(i)
			rank, idx = self.__seekers_player2agent[i]
			self.__seeker_team.set_percept(rank, idx, current_percept)

	def __transfer_hider_actions(self):
		for i in range(self.__hider_team.get_ranks()):
			for j in range(self.__hider_team.get_num_rankers(i)):
				rank, ai_idx = i, j
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

	def __update_simulation(self, dt):

		# extract percept from graphics layer and send to ai layer
		self.__transfer_hider_percepts()
		self.__transfer_seeker_percepts()

		# update the states in ai layer so that they selct actions
		self.__hider_team.select_actions()
		self.__seeker_team.select_actions()

		# extract action from ai layer and 
		# execute the above extracted action using graphics layer
		self.__transfer_hider_actions()
		self.__transfer_seeker_actions()


		# available_actions = list(action.Action)
		# for i in range(self.__num_hiders):
		# 	act = random.choice(available_actions)
		# 	self.__window.set_hider_action(i, act)

		# for i in range(1, self.__num_seekers):
		# 	act = random.choice(available_actions)
		# 	self.__window.set_seeker_action(i, act)
			
		self.__window.update(dt)

	def simulate(self):
		pyglet.clock.schedule_interval(self.__update_simulation, 1/60.)
		pyglet.app.run()
		



