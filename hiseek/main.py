import sys

import argparse

import experiment
import config

def main():
	parser = argparse.ArgumentParser(description="Medusa: Simulation of a massive hide and seek game")
	# 4 main modes of the game
	parser.add_argument("-v", "--visualisation", action="store_true", help=" This mode displays the simulation in a window but replay of the game is not saved in a file.")
	parser.add_argument("-s", "--simulation", action="store_true", help="This mode does not display the simulation but replay of the game is saved in a file.")
	parser.add_argument("-vs", "--vis_sim", action="store_true", help="This mode displays the simulation as well as saves the replay of the game in a file.")
	parser.add_argument("-r", "--replay", action="store_true", help="This mode replays the game of hide/seek stored in a replay file.")

	parser.add_argument("-n", "--num_runs", type=int, default = 1, help="Number of simulations to be performed.")
	parser.add_argument("-mh", "--mode_hiders", default = "random", help="Hider's mode, strategy to be used by the hider team during simulations.")
	parser.add_argument("-ms", "--mode_seekers", default = "random", help="Seeker's mode, strategy to be used by the seeker team during simulations.")
	parser.add_argument("-nh", "--num_hiders", type=int, default = 1, help="Number of hiders to be used in each simulation.")
	parser.add_argument("-ns", "--num_seekers", type=int, default = 1, help="Number of seekers to be used in each simulation")
	parser.add_argument("-m", "--map_id", type=int, default = 4)
	parser.add_argument("-i", "--input_file", default = "input.txt", help="Name of the input replay file to be visualised.")
	parser.add_argument("-o", "--output_file", default = "hs.replay", help="Name of output replay file of the game.")
	parser.add_argument("-f", "--fps", type=int, default = 60, help="Frames per second to be used during simulation.")
	parser.add_argument("-vel", "--velocity", type=int, default = 600, help="Velocity in pixels/sec of hider and seekers.")
	parser.add_argument("-ver", "--verbose", type=int, choices = [0, 1, 2], default = 0, help="Increase output verbosity")
	parser.add_argument("-tq", "--time_quanta", action="store_false", help="Sets time quanta, used for updating the players distance, to variable.(fixed/variable)")
	parser.add_argument("-nr", "--num_rays", type=int, default = 10, help="Number of rays to be used for calculating visibility region of an agent.")
	parser.add_argument("-va", "--visibility_angle", type=int, default = 45, help="Visibility angle")
	parser.add_argument("-hi", "--hider_image", default="dark_hider.png", help="Hider's image used during visualisations.")
	parser.add_argument("-si", "--seeker_image", default="dark_seeker.png", help="Seeker's image used during visualisations.")
	
	parser.add_argument("-sf", "--save_frame", action="store_true", help="This mode saves the rendered frames.")
	parser.add_argument("-sfel", "--show_fellows", action="store_true", help="(Use only when 'human' strategy is selected) Shows other team mates.")
	parser.add_argument("-sopp", "--show_opponent", action="store_true", help="(Use only when 'human' strategy is selected) Shows the opponent agents.")
	
	parser.add_argument("-tex", "--texture_flag", action="store_true", help="Enables the usage of textures.")
	parser.add_argument("-full", "--full_screen", action="store_true", help="Starts display in full screen mode.")

	args = parser.parse_args()

	# Need to have a trainer class which trains on input and provides its output to the experiment
	mode_count = 0
	if args.visualisation:
		mode_count += 1
	if args.simulation:
		mode_count += 1
	if args.vis_sim:
		mode_count += 1
	if args.replay:
		mode_count += 1

	safe_flag = True

	if mode_count > 1:
		print('More than one mode selected.')
		print('Select only one out of visualisation, simulation, vis_sim, replay')
		safe_flag = False

	if args.mode_hiders == 'human' and args.mode_seekers == 'human':
		print('Both Hider and Seeker cannot be in human modes')
		safe_flag = False

	if args.simulation and (args.mode_hiders == 'human' or args.mode_seekers == 'human'):
		print('Visualization needs to be enabled in human mode.')
		safe_flag = False

	if args.mode_hiders != 'human' and args.mode_seekers != 'human' and args.show_fellows:
		print('! WARNING: You have not selected human mode but selected show-fellows option.')
		print('! WARNING: Show fellows only effects hider or seeker visualization in human mode.')


	if safe_flag:
		if mode_count == 0:
			print('No mode selected, using vis_sim mode as default.')
			args.vis_sim = True
		conf_options = config.Configuration(int(args.fps), int(args.velocity), args.time_quanta, int(args.num_rays), int(args.visibility_angle), int(args.verbose), args.save_frame, args.hider_image, args.seeker_image, args.show_fellows, args.show_opponent, args.texture_flag, args.full_screen)
		exp = experiment.Experiment(args.visualisation, args.simulation, args.vis_sim, args.replay, args.num_runs, args.mode_hiders, args.mode_seekers, args.num_hiders, args.num_seekers, args.map_id, args.input_file, args.output_file, conf_options)
		exp.run()



if __name__ == '__main__':
    main()