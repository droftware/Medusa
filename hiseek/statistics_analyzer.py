import pickle
from mapmanager import StrategicPoint

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def main():
	statistic_file = 'hs_0_.statistic'
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
		square = patches.Rectangle(bottom, length, length, color='#4a235a',fill=True) 
		obstacles.append(square)

	
	sp_file_name = 'id_' + str(map_id) + '.st_pts'
	spfile = open(sp_file_name, 'rb')
	strategic_points = pickle.load(spfile)



	plt.style.use('dark_background')
	# plt.axis('off')

	fig3 = plt.figure()
	# ax3 = fig3.add_axes([0,0, map_width, map_length])
	ax3 = fig3.add_subplot(111, aspect='equal')
	ax3.set_xlim([0, map_width])
	ax3.set_ylim([0, map_length])
	ax3.axis('off')

	for p in obstacles:
		ax3.add_patch(p)
	circle_rad = 5
	for i in range(num_seekers):
		ax3.plot(seeker_paths_x[i], seeker_paths_y[i], 'y^')



	for i in range(num_hiders):
		ax3.plot(hider_paths_x[i], hider_paths_y[i], 'r*')


	for i in range(num_hiders):
		x = hider_paths_x[i][-1]
		y = hider_paths_y[i][-1]
		circle_rad = 10 # This is the radius, in points
		ax3.plot(x, y, 'o',
				ms=circle_rad * 2, mec='g', mfc='none', mew=2)

	for i in range(num_seekers):
		ax3.plot(seeker_paths_x[i][0], seeker_paths_y[i][0], 'b^', ms=circle_rad * 2, mec='orange', mfc='orange', mew=2)

	for i in range(num_hiders):
		ax3.plot(hider_paths_x[i][0], hider_paths_y[i][0], 'b*', ms=circle_rad * 2, mec='orange', mfc='orange', mew=2)

					
		



	fig3.savefig('rect3.png', dpi=90, bbox_inches='tight')
	# plt.show()
	# plt.savefig("example.png",bbox_inches='tight')

if __name__ == '__main__':
	main()