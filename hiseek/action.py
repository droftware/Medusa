
class Action:
	North = 1
	NorthEast = 2
	East = 3
	SouthEast = 4
	South = 5
	SouthWest = 6
	West = 7
	NorthWest = 8
	Stop = 9

	all_actions = [North, NorthEast, East, SouthEast, South, SouthWest, West, NorthWest, Stop]
	num_actions = len(all_actions)

ROTATION = {}
ROTATION[Action.North] = 270.001 
ROTATION[Action.NorthEast] = 315.001
ROTATION[Action.East] = 0.001
ROTATION[Action.SouthEast] = 45.001
ROTATION[Action.South] = 90.001
ROTATION[Action.SouthWest] = 135.001
ROTATION[Action.West] = 180.001
ROTATION[Action.NorthWest] = 225.001

