import functools

try:
    from ompl import base as ob
    from ompl import geometric as og
except:
    # if the ompl module is not in the PYTHONPATH assume it is installed in a
    # subdirectory of the parent directory called "py-bindings."
    from os.path import abspath, dirname, join
    import sys
    sys.path.insert(0, join(dirname(dirname(abspath(__file__))),'py-bindings'))
    from ompl import util as ou
    from ompl import base as ob
    from ompl import geometric as og

import coord

class BasicPlanner(object):

    def __init__(self, map_manager):
        self._map_manager = map_manager
        self._space = ob.SE2StateSpace()

        self._bounds = ob.RealVectorBounds(2)
        self._bounds.setLow(0)
        self._bounds.setHigh(0, self._map_manager.get_map().get_map_width())
        self._bounds.setHigh(1, self._map_manager.get_map().get_map_height())
        self._space.setBounds(self._bounds)

        self._setup = og.SimpleSetup(self._space)
        self._setup.setStateValidityChecker(ob.StateValidityCheckerFn(
            functools.partial(BasicPlanner.isStateValid, self)))

        self._path = None

    def plan_random_goal(self, start_coord):
        start_state = ob.State(self._setup.getStateSpace())
        start_state().setX(start_coord.get_x())
        start_state().setY(start_coord.get_y())
        goal_state = ob.State(self._setup.getStateSpace())
        goal_state.random()

        self.__solve_path(start_state, goal_state)

    def plan(self, start_coord, goal_coord):
        start_state = ob.State(self._setup.getStateSpace())
        start_state().setX(start_coord.get_x())
        start_state().setY(start_coord.get_y())
        goal_state = ob.State(self._setup.getStateSpace())
        goal_state().setX(goal_coord.get_x())
        goal_state().setY(goal_coord.get_y())

        self.__solve_path(start_state, goal_state)
        

    def __solve_path(self, start_state, goal_state):
        self._setup.setStartAndGoalStates(start_state, goal_state)

        solved = self._setup.solve(1.0)
        assert(solved)
        if solved:
            # try to shorten the path
            self._setup.simplifySolution()
            # print the simplified path
            self._path = self._setup.getSolutionPath()
            print(self._path)



    def isStateValid(self, state):
        state_position = coord.Coord(int(state.getX()), int(state.getY()))
        return not self._map_manager.get_map().check_obstacle_collision(state_position)

