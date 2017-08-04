import os

import simulator
import statistic
import replay
import test

class Experiment(object):
	"""
		Responsible for executing the simulations in the manner demanded by the user and 
		tracking the statistics involved
	"""

	def __init__(self, visualisation, simulation, vis_sim, replay, num_runs, mode_hiders, mode_seekers, num_hiders, num_seekers, map_id, input_file, output_file, fps, velocity, verbose, fixed_time_quanta):
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
		self.__fps = fps
		self.__velocity = velocity
		self.__verbose = verbose
		self.__fixed_time_quanta = fixed_time_quanta

	def run(self):
		if self.__replay:
			if os.path.isfile(self.__input_file):	
				rep = replay.Replay(self.__input_file, self.__fps, self.__velocity, self.__fixed_time_quanta)
				rep.run_replay()
			else:
				print('Replay file does not exist')
		elif self.__vis_sim:
			log_flag = True
			sim = simulator.Simulator(self.__mode_hiders, self.__mode_seekers, self.__num_hiders, self.__num_seekers, self.__map_id, self.__input_file, self.__output_file, self.__fps, self.__velocity, self.__verbose, self.__fixed_time_quanta, log_flag)
			sim.simulate()
		elif self.__visualisation:
			log_flag = False
			sim = simulator.Simulator(self.__mode_hiders, self.__mode_seekers, self.__num_hiders, self.__num_seekers, self.__map_id, self.__input_file, self.__output_file, self.__fps, self.__velocity, self.__verbose, self.__fixed_time_quanta, log_flag)
			sim.simulate()
		elif self.__simulation:
			print('Yet to be implemented')

				
