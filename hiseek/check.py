# # Checking map module
# import gamemap
# pm = gamemap.PolygonMap(0)
# print('Number of polygons:', pm.get_num_polygons())
# for i in range(pm.get_num_polygons()):
# 	print(pm.get_polygon(i))

import pyglet
import graphics
import gamemap

pm = gamemap.PolygonMap(0)
g = graphics.Graphics(640,360,2,2,pm)
pyglet.clock.schedule_interval(g.update, 1/60.)
pyglet.app.run()