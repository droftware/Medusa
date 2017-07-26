
class Action:
	North = 0
	NorthEast = 1
	East = 2
	SouthEast = 3
	South = 4
	SouthWest = 5
	West = 6
	NorthWest = 7
	Stop = 8

	all_actions = [North, NorthEast, East, SouthEast, South, SouthWest, West, NorthWest, Stop]
	num_actions = len(all_actions)

	action2string = {}
	string2action = {}

	string2action["North"] = North
	string2action["NorthEast"] = NorthEast
	string2action["East"] = East
	string2action["SouthEast"] = SouthEast
	string2action["South"] = South
	string2action["SouthWest"] = SouthWest
	string2action["West"] = West
	string2action["NorthWest"] = NorthWest
	string2action["Stop"] = Stop

	action2string[North] = "North"
	action2string[NorthEast] = "NorthEast"
	action2string[East] = "East"
	action2string[SouthEast] = "SouthEast"
	action2string[South] = "South"
	action2string[SouthWest] = "SouthWest"
	action2string[West] = "West"
	action2string[NorthWest] = "NorthWest"
	action2string[Stop] = "Stop"

ROTATION = [None] * (Action.num_actions-1)
ROTATION[Action.North] = 270.001 
ROTATION[Action.NorthEast] = 315.001
ROTATION[Action.East] = 0.001
ROTATION[Action.SouthEast] = 45.001
ROTATION[Action.South] = 90.001
ROTATION[Action.SouthWest] = 135.001
ROTATION[Action.West] = 180.001
ROTATION[Action.NorthWest] = 225.001

