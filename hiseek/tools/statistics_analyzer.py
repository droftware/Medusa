import matplotlib.pyplot as plt
import matplotlib.patches as patches

def main():
	statistic_file = 'hs.statistic'
	map_file = None
	sf = open(statistic_file, 'r')
	print('File opened')
	map_id = None
	num_hiders = None
	num_seekers = None
	token = None


	while True:
		token = sf.readline().strip()
		if token == 'hider_paths:':
			break
		pre_token = token.split(':')[0]
		post_token = token.split(':')[1]
		if pre_token == 'map_id':
			map_id = int(post_token)
		elif pre_token == 'num_hiders':
			num_hiders = int(post_token)
		elif pre_token == 'num_seekers':
			num_seekers = int(post_token)
		else:
			print('PARSING FAILED')

	map_file = 'id_' + str(map_id) + '.polygons'

	hider_paths_x = [[] for i in range(num_hiders)]
	hider_paths_y = [[] for i in range(num_hiders)]

	for i in range(num_hiders):
		token = sf.readline().strip()
		position_list = token.split(';')
		for position in position_list:
			position = position.split(',')
			hider_paths_x[i].append(float(position[0]))
			hider_paths_y[i].append(float(position[1]))

	# # Print paths
	# for i in range(num_hiders):
	# 	print()
	# 	print('Hider:',i)
	# 	print('x path:', hider_paths_x[i])
	# 	print('y path:', hider_paths_y[i])

	token = sf.readline().strip()
	assert(token == 'seeker_paths:')

	seeker_paths_x = [[] for i in range(num_seekers)]
	seeker_paths_y = [[] for i in range(num_seekers)]

	for i in range(num_seekers):
		token = sf.readline().strip()
		position_list = token.split(';')
		for position in position_list:
			position = position.split(',')
			seeker_paths_x[i].append(float(position[0]))
			seeker_paths_y[i].append(float(position[1]))

	# for i in range(num_seekers):
	# 	print()
	# 	print('Seeker:',i)
	# 	print('x path:', seeker_paths_x[i])
	# 	print('y path:', seeker_paths_y[i])

	caught_times = [0 for i in range(num_hiders)]
	
	token = sf.readline().strip()
	assert(token == 'caught_times:')

	for i in range(num_hiders):
		token = sf.readline().strip()
		caught_times[i] = int(token)

	for i in range(num_hiders):
		print('Hider:',i,' was caught at:', caught_times[i]) 

	sf.close()

	with open(map_file) as mf:
		tokens = mf.readlines()

	boundary = tokens[0].strip().split(',')
	map_width = int(boundary[0])
	map_length = int(boundary[1])

	print('Map boundary:', map_width, map_length)

	obstacles = []

	for token in tokens[1:]:
		token = token.split(':')[1].split(',')
		# print('Token:', token)
		centre = (int(token[0]), int(token[1]))
		length = int(token[2])
		bottom = (centre[0] - length/2.0, centre[1] - length/2.0)
		print('Bottom:', bottom, 'length:', length)
		square = patches.Rectangle(bottom, length, length, hatch='\\', fill=False) 
		obstacles.append(square)

	# obstacles = [
	#     patches.Rectangle(
	#         (0.1, 0.1), 0.3, 0.6,
	#         hatch='/'
	#     ),
	#     patches.Rectangle(
	#         (0.5, 0.1), 0.3, 0.6,
	#         hatch='\\',
	#         fill=False
	#     ),
	# ]

	fig3 = plt.figure()
	# ax3 = fig3.add_axes([0,0, map_width, map_length])
	ax3 = fig3.add_subplot(111, aspect='equal')
	ax3.set_xlim([0, map_width])
	ax3.set_ylim([0, map_length])

	for p in obstacles:
		ax3.add_patch(p)
	ax3.plot(seeker_paths_x, seeker_paths_y, 'bo')
	# fig3.savefig('rect3.png', dpi=90, bbox_inches='tight')
	plt.show()

if __name__ == '__main__':
	main()