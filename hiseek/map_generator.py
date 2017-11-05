import shapes
import sys
import random

def main():
	width = int(sys.argv[1])
	height = int(sys.argv[2])
	max_squares = int(sys.argv[3])
	min_length = 70
	max_length = 100
	squares_list = []
	sq = shapes.Square((10, 10), 20)
	squares_list.append(sq)
	num_squares = 0
	while num_squares < max_squares:
		sq_valid = False
		while not sq_valid:
			cx = random.randint(0, width - 1)
			cy = random.randint(0, height - 1)
			length = random.randint(min_length, max_length)
			sq = shapes.Square((cx, cy), length)
			collision = False
			for other in squares_list:
				if sq.check_aabb_collision(other):
					collision = True
					break
			if not collision:
				squares_list.append(sq)
				sq_valid = True
				num_squares += 1

	# for sqs in squares_list:
	# 	print(sqs)

	f = open('id_3.polygons', 'w')
	f.write(str(width)+', '+str(height) + '\n')
	for sqs in squares_list[1:]:
		centre = sqs.get_centre()
		length = sqs.get_length()
		token = 'square: ' + str(centre[0]) + ', ' + str(centre[1]) + ', ' + str(length) +'\n'
		f.write(token)
	f.close()





if __name__ == '__main__':
	main()