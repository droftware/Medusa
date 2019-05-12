import shapes
import sys
import random
import os

# SampleInput: python2 map_generator.py 600 500 30 25 id_10.polygons

def main():
	width = int(sys.argv[1]) 
	height = int(sys.argv[2])
	max_obstacles = int(sys.argv[3])
	num_approx_points = int(sys.argv[4])
	file_name = str(sys.argv[5])

	if os.path.exists(file_name):
		print('The map with the give name already exists. Please delete it manually before proceeding to overwrite it.')

	boundary_offset = 10
	min_length = 40
	max_length = 70
	obstacles_list = []
	obstacles_type = []

	# Dummy obstacle to prevent the starting point of seekers 
	# from getting blocked by some obstacle
	obs = shapes.Square((30, 30), 60)
	obstacles_list.append(obs)
	obstacles_type.append('square')

	num_obstacles = 0
	while num_obstacles < max_obstacles:
		obs_valid = False
		while not obs_valid:
			cx = random.randint(max_length+boundary_offset, width - max_length - boundary_offset)
			cy = random.randint(max_length+boundary_offset, height - max_length - boundary_offset)
			length = random.randint(min_length, max_length)
			choice = random.randint(0, 1)
			choice = 1
			if choice == 0:
				obs = shapes.Square((cx, cy), length)
				obs_type = 'square'
			else:
				obs = shapes.Circle((cx, cy), length, num_approx_points)
				obs_type = 'circle'

			collision = False
			for other in obstacles_list:
				if obs.check_aabb_collision(other,20):
					collision = True
					break
			if not collision:
				obstacles_list.append(obs)
				obstacles_type.append(obs_type)
				obs_valid = True
				num_obstacles += 1

	f = open(file_name, 'w+')

	f.write(str(width)+', '+str(height) + '\n')
	for obs, obs_type in zip(obstacles_list[1:], obstacles_type[1:]):
		centre = obs.get_centre()
		token = obs_type + ': ' + str(centre[0]) + ', ' + str(centre[1])
		if obs_type == 'circle':
			token += ', ' + str(obs.get_radius()) + ',' + str(num_approx_points)
		elif obs_type == 'square':
			token += ', ' + str(obs.get_length())

		token += '\n'
		f.write(token)

if __name__ == '__main__':
	main()
