import argparse
import experiment

def main():
	parser = argparse.ArgumentParser(description="Hiseek: Simulation of a massive hide and seek game")
	parser.add_argument("-d", "--display", action="store_true", help="Display the simulations.")
	parser.add_argument("-t", "--train", action="store_true", help="Train the model.")
	parser.add_argument("-n", "--num_runs", type=int, default = 1, help="Number of simulations to be performed.")
	parser.add_argument("-mh", "--mode_hiders", default = "random", help="Hider's mode, strategy to be used by the hider team during simulations.")
	parser.add_argument("-ms", "--mode_seekers", default = "random", help="Seeker's mode, strategy to be used by the seeker team during simulations.")
	parser.add_argument("-nh", "--num_hiders", type=int, default = 1, help="Number of hiders to be used in each simulation.")
	parser.add_argument("-ns", "--num_seekers", type=int, default = 1, help="Number of seekers to be used in each simulation")
	parser.add_argument("-m", "--map_id", type=int, choices = [0, 1], default = 0)
	parser.add_argument("-i", "--input_file", default = ".", help="Input file")
	parser.add_argument("-o", "--output_file", default = ".", help="Output file")
	parser.add_argument("-v", "--verbose", type=int, choices = [0, 1, 2], default = 0, help="Increase output verbosity")
	args = parser.parse_args()

	# Need to have a trainer class which trains on input and provides its output to the experiment

	exp = experiment.Experiment(args.display, args.num_runs, args.mode_hiders, args.mode_seekers, args.num_hiders, args.num_seekers, args.map_id, args.input_file, args.output_file, args.verbose)
	exp.run()

	print('Hello world')

if __name__ == '__main__':
    main()