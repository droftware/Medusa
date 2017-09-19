import numpy as np
import copy
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

def get_distance(visibility_map, x1, y1, x2, y2):
	return abs(visibility_map[x1, y1] - visibility_map[x2, y2])

def check_legal(visibility_map, x, y):
	if x > 0 and x < visibility_map.shape[0] - 1:
		if y > 0 and y < visibility_map.shape[1] - 1:
			if visibility_map[x, y] != -1:
				return True
	return False


def region_query(visibility_map, x, y, eps):
	neighbourhood = []

	for i in range(-1, 2):
		for j in range(-1, 2):
			if i == 0 and j == 0:
				continue
			a, b = x + i, y + j
			if check_legal(visibility_map, a, b):
				if get_distance(visibility_map, a, b, x, y) < eps:
					# print('appending', a,b, 'to neighbourhood - '),
					neighbourhood.append((a,b))
	# print()

	return neighbourhood

def dbscan(file_name, eps, minPts):
	UNDEFINED = 0
	NOISE = -1

	visibility_map = np.loadtxt(file_name)
	visibility_map = visibility_map.astype('int')

	num_rows = visibility_map.shape[0]
	num_cols = visibility_map.shape[1]

	label = np.zeros((num_rows, num_cols))
	cluster = 0

	for i in range(num_rows):
		for j in range(num_cols):
			if not check_legal(visibility_map, i, j):
				continue
			if label[i, j] == UNDEFINED:
				print('')
				print('Label:', i,j ,' is UNDEFINED')
				neighbourhood = region_query(visibility_map, i, j , eps)
				print('Its neighbours are:', neighbourhood)
				if len(neighbourhood) + 1 < minPts:
					label[i, j] = NOISE
				else:
					cluster += 1
					label[i, j] = cluster
					idx = 0
					while idx < len(neighbourhood):
						# print('*:', neighbourhood)
						neighbour = neighbourhood[idx]
						print('Exploring neighbour:', neighbour)
						ni, nj = neighbour[0], neighbour[1] 
						if label[ni, nj] == NOISE:
							print('Its NOISE')
							label[ni, nj] = cluster
						if label[ni, nj] == UNDEFINED:
							print('Assigning it to current cluster')
							label[ni, nj] = cluster
							nextNeighbourhood = region_query(visibility_map, ni, nj, eps)
							print('Neighbours of:', neighbour, 'are:', nextNeighbourhood)
							if len(nextNeighbourhood) >= minPts:
								print('Appending neighbour\'s neighbours')
								neighbourhood = neighbourhood + copy.deepcopy(nextNeighbourhood)
						idx += 1

	label = label.astype('int')
	return label, cluster

def main():
	file_name = 'id_4.obstruction'
	eps = 100
	minPts = 8
	label, num_clusters = dbscan(file_name, eps, minPts)
	print('Clustering done')
	np.savetxt(file_name.split('.')[0] + '.clusters', label)
	print('File saved')
	# print(label)
	print('Number of clusters:', num_clusters)

	f, ax = plt.subplots(figsize=(label.shape[0], label.shape[1]))
	sns.heatmap(label, annot=True, fmt="d", linewidths=.5, ax=ax)
	plt.savefig(file_name.split('.')[0]+ '_clusters')


if __name__ == '__main__':
    main()

