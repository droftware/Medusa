import sys
import random
import math

import shapes

def main():
	num_rows = int(sys.argv[1])
	num_cols = int(sys.argv[2])
	gap = int(sys.argv[3])
	map_width = 1500
	map_height = 315
	# Block is rectangular not square
	block_width = math.floor((map_width - (1+num_cols)*gap)/(num_cols*1.0))
	# block_height = floor((map_height - (1+num_cols)*gap)/num_cols)
	block_height = block_width
	cx = gap + block_width/2.0
	cy = gap + block_height/2.0
	squares_list = []
	
	for i in range(num_rows):
		for j in range(num_cols):
			sq = shapes.Square((int(cx), int(cy)), int(block_width))		
			squares_list.append(sq)
			cx += (block_width + gap)
		cy += (gap + block_height)
		cx = gap + block_width/2.0


	f = open('id_8.polygons', 'w')
	f.write(str(map_width)+', '+str(map_height) + '\n')
	for sqs in squares_list:
		centre = sqs.get_centre()
		length = sqs.get_length()
		token = 'square: ' + str(centre[0]) + ', ' + str(centre[1]) + ', ' + str(length) +'\n'
		f.write(token)
	f.close()





if __name__ == '__main__':
	main()