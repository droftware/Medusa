import random

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

		self.__window_width = window_width
		self.__window_height = window_height
		self.__window = graphics.Graphics(window_width, window_height, num_hiders, num_seekers, self.__map)
		

	def __update_simulation(self, dt):
		available_actions = list(action.Action)

		for i in range(self.__num_hiders):
			act = random.choice(available_actions)
			self.__window.set_hider_action(i, act)

		for i in range(self.__num_seekers):
			act = random.choice(available_actions)
			self.__window.set_seeker_action(i, act)
		print('Updated')
		self.__window.update(dt)

	def simulate(self):
		pyglet.clock.schedule_interval(self.__update_simulation, 1/60.)
		pyglet.app.run()
		



