import math
import random 

import pyglet
from pyglet.window import key

import shapes
import coord

ARENA_WIDTH = 640
ARENA_HEIGHT = 360
PLAYER_SPIN_SPEED = 360.
PLAYER_ACCEL = 200.

window = pyglet.window.Window(ARENA_WIDTH, ARENA_HEIGHT)

pyglet.resource.path.append('resources')
pyglet.resource.reindex()

def center_anchor(img):
	img.anchor_x = img.width // 2
	img.anchor_y = img.height // 2

def to_radians(degrees):
	return math.pi * degrees / 180.0

def get_intersection(ray, segment):
	pass

class Player(pyglet.sprite.Sprite, key.KeyStateHandler):
	def __init__(self, img, batch, pos_x, pos_y):
		super(Player, self).__init__(img, pos_x, pos_y, batch=batch)
		center_anchor(img)
		self.dx = 0
		self.dy = 0
		self.rotation_x = 0
		self.rotation_y = 0

	def get_rotation_x(self):
		return self.rotation_x

	def get_rotation_y(self):
		return self.rotation_y

	def get_rotation(self):
		return self.rotation

	def get_x(self):
		return self.x

	def get_y(self):
		return self.y

	def update(self, dt):
		# Update rotation
		# print('Reached update:',dt)

		if self[key.LEFT]:
			self.rotation -= PLAYER_SPIN_SPEED * dt
			# print('Left key pressed')
		if self[key.RIGHT]:
			self.rotation += PLAYER_SPIN_SPEED * dt
			# print('Right key pressed')
		# print('Rotation:', self.rotation)

		# Get x/y components of orientation
		self.rotation_x = math.cos(to_radians(-self.rotation))
		self.rotation_y = math.sin(to_radians(-self.rotation))

		# Update velocity
		if self[key.UP]:
			self.dx += PLAYER_ACCEL * self.rotation_x * dt
			self.dy += PLAYER_ACCEL * self.rotation_y * dt

		self.x = self.x + self.dx * dt
		self.y = self.y + self.dy * dt
		
class Dummy(pyglet.sprite.Sprite):
	def __init__(self, img, batch):
		super(Dummy, self).__init__(img, random.random() * ARENA_WIDTH, random.random() * ARENA_HEIGHT, batch=batch)
		center_anchor(img)

	def update(self, dt):
		self.x += random.random() * 0.5
		self.y += random.random() * 0.5


def line_update(player, polygons, visibility_polygon):
	c = coord.Coord(player.get_x(), player.get_y())
	player_rotation = player.get_rotation()

	vis_points = [int(c.get_x()), int(c.get_y())]

	
	visibility_angle = 45
	num_rays = 10

	rotation = player_rotation - visibility_angle
	idx = 0
	offset = (visibility_angle * 2.0)/num_rays
	while rotation < player_rotation + visibility_angle:
		# print('idx:', idx, 'Rotation:', rotation)
		rotation_x = math.cos(to_radians(-rotation))
		rotation_y = math.sin(to_radians(-rotation))
		r = coord.Coord(player.get_x()+rotation_x, player.get_y()+rotation_y)

		ray = shapes.Line(c, r)
		# line_vertices.vertices = [int(c.get_x()), int(c.get_y()), int(r.get_x()), int(r.get_y())]
		closest_intersect = None
		for polygon in polygons:
			for i in range(polygon.get_num_lines()):
				intersect = shapes.Line.get_intersection(ray, polygon.get_line(i))
				if not intersect:
					continue
				if not closest_intersect or intersect[1] < closest_intersect[1]:
					closest_intersect = intersect

		# print(closest_intersect[0])
		vis_points.append(int(closest_intersect[0].get_x()))
		vis_points.append(int(closest_intersect[0].get_y()))

		# final_line = shapes.Line(c, closest_intersect[0])
		# a_x = int(final_line.get_a().get_x()) 
		# a_y = int(final_line.get_a().get_y())
		# b_x = int(final_line.get_b().get_x())
		# b_y = int(final_line.get_b().get_y())
		# line_vertices[idx].vertices = [a_x, a_y, b_x, b_y]

		rotation += offset
		idx += 1

	visibility_polygon.vertices = tuple(vis_points)

background = pyglet.graphics.OrderedGroup(0)
foreground = pyglet.graphics.OrderedGroup(1)

batch = pyglet.graphics.Batch()
seeker_img = pyglet.resource.image('seeker.png')
wanderer_img = pyglet.resource.image('wanderer.png')
player = Player(wanderer_img, batch, ARENA_WIDTH//2, ARENA_HEIGHT//2)
hider = Player(seeker_img, batch, 15, 15)

window.push_handlers(player)

# line_vertices = [batch.add_indexed(2, pyglet.gl.GL_LINES, background, 
# 		[0,1],
# 		('v2i', (player.get_x(), player.get_y(), 
# 			10*player.get_rotation_x(), 10*player.get_rotation_y() ) ),
# ) for i in range(10)]

color_list = []
for i in range(11):
	# 149, 165, 166
	color_list.append(149)
	color_list.append(165)
	color_list.append(166)
color_tuple = tuple(color_list)
visibility_polygon = batch.add_indexed(11, pyglet.gl.GL_TRIANGLES, background, 
		[0,1,2, 0,2,3, 0,3,4, 0,4,5, 0,5,6, 0,6,7, 0,7,8, 0,8,9, 0,9,10],
		('v2i', tuple([0 for i in range(22)])),
		('c3B', color_tuple)
		)

# batch.add_indexed(11, pyglet.gl.GL_LINES, background, 
# 		[0,1,1,2,2,3,3,0],
# 		('v2i', tuple([0 for i in range(22)]) ),)
# hole_img = pyglet.resource.image('blackhole.png')
# dummies = [Dummy(hole_img, batch) for i in range(100)]

polygons = []
polygons.append(shapes.Polygon((0, 0, 640, 0, 640, 360, 0, 360)))
polygons.append(shapes.Polygon((100, 150, 120, 50, 200, 80, 140, 210)))
polygons.append(shapes.Polygon((100, 200, 120, 250, 60, 300)))
polygons.append(shapes.Polygon((200, 260, 220,150, 300,200, 350, 320)))
polygons.append(shapes.Polygon((340, 60, 360, 40, 370, 70)))
polygons.append(shapes.Polygon((450, 190, 560, 170, 540, 270, 430, 290)))
polygons.append(shapes.Polygon((400, 95, 580, 50, 480, 150)))

# for i in range(len(polygons)):
# 	print(polygons[i])

for i in range(len(polygons)):
	if polygons[i].get_num_vertices() == 4:
		batch.add_indexed(4, pyglet.gl.GL_LINES, background, 
		[0,1,1,2,2,3,3,0],
		('v2i', polygons[i].get_points_tuple()),)
	if polygons[i].get_num_vertices() == 3:
		batch.add_indexed(3, pyglet.gl.GL_LINES, background, 
		[0,1,1,2,2,0],
		('v2i', polygons[i].get_points_tuple() ),)


@window.event
def on_draw():
	window.clear()
	batch.draw()


def update(dt):
	# Move 10 pixels per second
	player.update(dt)
	hider.update(dt)
	line_update(player, polygons, visibility_polygon)
	# for i in range(len(dummies)):
	# 	dummies[i].update(dt)

# Call update 60 times a second
pyglet.clock.schedule_interval(update, 1/60.)


pyglet.app.run()