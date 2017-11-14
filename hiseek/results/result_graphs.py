import pickle


import matplotlib.pyplot as plt
import matplotlib.patches as patches

def get_caught_times(strat_file_name):
	statistic_file = strat_file_name
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

	caught_times.sort()
	return caught_times

def main():
	max_files = 100
	num_hiders = 30
	hider_game_times = [[] for j in range(num_hiders)]
	for i in range(max_files):
		name = 'hs_' + str(i) + '_.statistic'
		caught_times = get_caught_times(name)
		game_completion_time = caught_times[-1]
		normalized_caught_times = [x*1.0/game_completion_time for x in caught_times]
		for j in range(num_hiders):
			hider_game_times[j].append(normalized_caught_times[j])
	print('Hider game times:')
	for i in range(num_hiders):
		print('i:',i,hider_game_times[i])

	print('Hider offsets')
	poffset = 0.90
	hider_offsets = [0 for j in range(num_hiders)]
	for i in range(num_hiders):
		sumh = 0
		for x in hider_game_times[i]:
			if x <= poffset:
				sumh += 1
		hider_offsets[i] = sumh
		print('i:',i,sumh)




if __name__ == '__main__':
    main()
