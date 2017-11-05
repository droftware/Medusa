import os

import simulator
import statistic
import replay
# import test

class Experiment(object):
	"""
		Responsible for executing the simulations in the manner demanded by the user and 
		tracking the statistics involved
	"""

	def __init__(self, visualisation, simulation, vis_sim, replay, num_runs, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, conf_options):
		self.__visualisation = visualisation
		self.__simulation = simulation
		self.__vis_sim = vis_sim
		self.__replay = replay

		self.__num_runs = num_runs
		self.__mode_hiders = mode_hiders
		self.__mode_seekers = mode_seekers
		self.__num_hiders = num_hiders
		self.__num_seekers = num_seekers
		self.__map_id = map_id
		self.__input_file = input_file
		self.__output_file = output_file
		self.__conf_options = conf_options

		self._total_step_times = []

	def run(self):
		if self.__replay:
			if os.path.isfile(self.__input_file):	
				rep = replay.Replay(self.__input_file, self.__conf_options)
				rep.run_replay()
			else:
				print('Replay file does not exist')
		else:
			if self.__vis_sim:
				log_flag = True
				vis_flag = True
			elif self.__visualisation:
				log_flag = False
				vis_flag = True
			elif self.__simulation:
				log_flag = True
				vis_flag = False
			for i in range(self.__num_runs):
				print()
				print('*** New game ***',i)
				sim = simulator.Simulator(self.__mode_hiders, self.__mode_seekers, self.__num_hiders, self.__num_seekers, self.__map_id, self.__input_file, self.__output_file, self.__conf_options, log_flag, vis_flag, self._total_step_times)
				sim.simulate()

			print('Step times:', self._total_step_times)
			sum_steps = 0
			for step in self._total_step_times:
				sum_steps += step
			avg_steps = sum_steps*1.0/self.__num_runs
			print('Average step time:', avg_steps)


			