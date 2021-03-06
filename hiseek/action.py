import math

import coord
import vector

class Action:
	N = 0
	NNE = 1
	NE = 2
	ENE = 3
	E = 4
	ESE = 5 
	SE = 6
	SSE = 7
	S = 8
	SSW = 9 
	SW = 10
	WSW = 11
	W = 12
	WNW = 13 
	NW = 14
	NNW = 15
	ST = 16

	all_directions = [E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW, N, NNE, NE, ENE]
	num_directions = len(all_directions)

	all_actions = all_directions + [ST]
	major_actions = [N, NE, E, SE, S, SW, W, NW]
	num_actions = len(all_actions)

	action2string = {}
	string2action = {}
	key2action = {}

	string2action["N"] = N
	string2action["NNE"] = NNE
	string2action["NE"] = NE
	string2action["ENE"] = ENE
	string2action["E"] = E
	string2action["ESE"] = ESE
	string2action["SE"] = SE
	string2action["SSE"] = SSE
	string2action["S"] = S
	string2action["SSW"] = SSW
	string2action["SW"] = SW
	string2action["WSW"] = WSW
	string2action["W"] = W
	string2action["WNW"] = WNW
	string2action["NW"] = NW
	string2action["NNW"] = NNW
	string2action["ST"] = ST

	action2string[N] = "N"
	action2string[NNE] = "NNE"
	action2string[NE] = "NE"
	action2string[ENE] = "ENE"
	action2string[E] = "E"
	action2string[ESE] = "ESE"
	action2string[SE] = "SE"
	action2string[SSE] = "SSE"
	action2string[S] = "S"
	action2string[SSW] = "SSW"
	action2string[SW] = "SW"
	action2string[WSW] = "WSW"
	action2string[W] = "W"
	action2string[WNW] = "WNW"
	action2string[NW] = "NW"
	action2string[NNW] = "NNW"
	action2string[ST] = "ST"

	key2action["NONE"] = ST
	key2action["UP"] = N
	key2action["DOWN"] = S
	key2action["RIGHT"] = E
	key2action["LEFT"] = W


# Rotation and vector mappings
ROTATION = [None] * (Action.num_actions - 1)
VECTOR = [None] * (Action.num_actions - 1)

offset_angle = 22.5
current_angle = 0.00001
for act in Action.all_actions:
	if act != Action.ST:
		ROTATION[act] = current_angle 
		x = math.cos(coord.Coord.to_radians(-current_angle))
		y = math.sin(coord.Coord.to_radians(-current_angle))
		VECTOR[act] = vector.Vector2D(x, y)
		VECTOR[act].normalize()
		current_angle += offset_angle

OBLIQUE_DIR_CLOCKWISE = [None] * (Action.num_actions - 1)
OBLIQUE_DIR_ANTI_CLOCKWISE = [None] * (Action.num_actions - 1)

for idx in range(Action.num_directions):
	act = Action.all_directions[idx]
	jdx = (idx+4)%Action.num_directions
	OBLIQUE_DIR_CLOCKWISE[act] = Action.all_directions[jdx]
	jdx = (idx-4)
	if jdx < 0:
		jdx += Action.num_directions
	OBLIQUE_DIR_ANTI_CLOCKWISE[act] = Action.all_directions[jdx] 


# for i in range(Action.num_actions):
# 	if i != Action.ST:
# 		print(Action.action2string[i], '-->', ROTATION[i], '-->', str(VECTOR[i]))
