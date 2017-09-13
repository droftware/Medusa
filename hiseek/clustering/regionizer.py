import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

file_name = 'id_3.obstruction'
visibility_map = np.loadtxt(file_name)
visibility_map = visibility_map.astype('int')

num_rows = visibility_map.shape[0]
num_cols = visibility_map.shape[1]
n = num_rows * num_cols

# Creating the weight matrix of similarity graph
W = np.zeros((n, n))
print('Creating W matrix')
for i in range(num_rows):
	for j in range(num_cols):
		print('')
		if visibility_map[i, j] != -1:
			print('Value of',i,j,' is:', visibility_map[i, j])
			right = i+1, j
			down = i, j+1
			node1 = (i * num_cols) + j
			if right[0] < num_rows and right[1] <  num_cols and visibility_map[right[0], right[1]] != -1:
				print('Evaluating right edge')
				node2 = (right[0] * num_cols) + right[1]
				print('Value of', right[0], right[1], 'is:', visibility_map[right[0], right[1]])
				val = abs(visibility_map[i, j] - visibility_map[right[0], right[1]]) * 1.0
				if val == 0:
					print('right val is 0')
					print(visibility_map[i, j], visibility_map[right[0], right[1]])
					val = 1
				W[node1, node2] = 1/val
				print('Right: Assigning val', W[node1, node2], 'to:', i,j,':',right)
			if down[0] < num_rows and down[1] < num_cols and visibility_map[down[0], down[1]] != -1:
				print('Evaluating down edge')
				node2 = (down[0] * num_cols) + down[1]
				print('Value of', down[0], down[1], 'is:', visibility_map[down[0], down[1]])

				val = abs(visibility_map[i, j] - visibility_map[down[0], down[1]]) * 1.0
				if val == 0:
					print('Down val is 0')
					print(visibility_map[i, j], visibility_map[down[0], down[1]])

					val = 1
				W[node1, node2] = 1/val
				print('Down: Assigning val', W[node1, node2], 'to:', i,j, down)

print('Saving W matrix')
np.savetxt('W.mtx', W)


# Computing the D matrix
D = np.zeros((n, n))
print('Creating D matrix')
for i in range(n):
	wt = 0
	for j,k in [(1,0), (-1,0), (0,1), (0,-1)]:
		idx = i + j, i + k
		if idx[0] >=0 and idx[0] < num_rows:
			if idx[1] >=0 and idx[1] < num_cols:
				wt += W[idx[0], idx[1]]
	D[i,i] = wt
print('Saving D matrix')
np.savetxt('D.mtx', D)


# Computing the graph laplacian matrix
print('Computing L matrix')
L = np.subtract(D, W)
print('Savinf L matrix')
np.savetxt('L.mtx', L)

print('Computing eigen vectors and vals')
eigen_vals, eigen_vecs = LA.eig(L)
print('Saving eigen vector and vals')
np.savetxt('eigen_vals.mtx', eigen_vals)
np.savetxt('eigen_vecs.mtx', eigen_vecs)





