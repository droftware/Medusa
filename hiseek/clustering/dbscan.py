import numpy as np
import copy

def get_distance(visibility_map, x1, y1, x2, y2):
	return abs(visibility_map[x1, y1] - visibility_map[x2, y2])

def check_legal(visibility_map, x, y):
	if x >= 0 and x < visibility_map.shape[0]:
		if y >= 0 and y < visibility_map.shape[1]:
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
					neighbourhood.append((a,b))

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
			if label[i, j] == UNDEFINED:
				neighbourhood = region_query(visibility_map, i, j , eps)
				if len(neighbourhood) + 1 < minPts:
					label[i, j] = NOISE
				else:
					cluster += 1
					label[i, j] = cluster
					for neighbur in neighbourhood:
						ni, nj = neighbur[0], neighbur[1] 
						if label[ni, nj] == NOISE:
							label[ni, nj] = cluster
						if label[ni, nj] == UNDEFINED:
							label[ni, nj] = cluster
							nextNeighbourhood = region_query(visibility_map, ni, nj, eps)
							if len(nextNeighbourhood) >= minPts:
								neighbourhood = neighbourhood + copy.deepcopy(nextNeighbourhood)

	return label

def main():
	file_name = 'id_3.obstruction'
	label = dbscan(file_name)
if __name__ == '__main__':
    main()

