import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

file_name = 'id_4.obstruction'
heat_map = np.loadtxt(file_name)
heat_map = heat_map.astype('int')

num_rows = heat_map.shape[0]
num_cols = heat_map.shape[1]

# Draw a heatmap with the numeric values in each cell
f, ax = plt.subplots(figsize=(num_rows, num_cols))
sns.heatmap(heat_map, annot=True, fmt="d", linewidths=.5, ax=ax)
plt.savefig(file_name.split('.')[0] + '_' + file_name.split('.')[1] )
