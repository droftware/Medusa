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
        # self._space = ob.SE2StateSpace()
        self._space = ob.RealVectorStateSpace()
        self._space.addDimension(0.0, self._map_manager.get_map().get_map_width())
        self._space.addDimension(0.0, self._map_manager.get_map().get_map_height())

        self._setup = og.SimpleSetup(self._space)
        self._setup.setStateValidityChecker(ob.StateValidityCheckerFn(
            functools.partial(BasicPlanner.isStateValid, self)))

        self._si = self._setup.getSpaceInformation()
        self._si.setStateValidityCheckingResolution(1.0 / self._space.getMaximumExtent())
        self._planner = og.RRTConnect(self._si)

        self._setup.setPlanner(self._planner)
        self._space.setup()


        self._path = None
        self.__next_idx = 1
        self._num_states = 0

    def get_paths_next_coord(self):
        # print('Entered get_paths_next_coord')
        # print('Path length:', self._path.length())
        # print('Next idx:', self.__next_idx)
        if self._path == None:
            # print('No path, thus returning None')
            return None
        if self.__next_idx >= self._num_states:
            # print('Next idx greater, retuning None')
            return None
        else:
            # print('Entered else:')
            state = self._path.getState(self.__next_idx)
            # print('Got state')
            state_position = coord.Coord(int(state[0]), int(state[1]))
            self.__next_idx += 1
            # print('Returning state pos:', str(state_position))
            return state_position


    def plan_random_goal(self, start_coord):
        start_state = ob.State(self._setup.getStateSpace())
        start_state()[0] = start_coord.get_x()
        start_state()[1] = start_coord.get_y()

        goal_state = ob.State(self._setup.getStateSpace())
        valid = False
        while not valid:
            goal_state.random()
            valid = self.isStateValid(goal_state())
            # if not valid:
            #     print('!! Random state not valid')
            # else:
            #     print('** Random state valid')

        self.__solve_path(start_state, goal_state)

    def plan(self, start_coord, goal_coord):
        '''
            Returns True if path is found, False otherwise
        '''
        start_state = ob.State(self._setup.getStateSpace())
        start_state()[0] = start_coord.get_x()
        start_state()[1] = start_coord.get_y()

        goal_state = ob.State(self._setup.getStateSpace())
        goal_state()[0] = goal_coord.get_x()
        goal_state()[1] = goal_coord.get_y()


        return self.__solve_path(start_state, goal_state)
        

    def __solve_path(self, start_state, goal_state):
        self._setup.setStartAndGoalStates(start_state, goal_state)

        for i in range(2):
            if self._setup.getPlanner():
                self._setup.getPlanner().clear()
            self._setup.solve()

        # assert(self._setup.haveSolutionPath())
        if self._setup.haveSolutionPath():
            # try to shorten the path
            self._setup.simplifySolution()
            # print the simplified path
            self._path = self._setup.getSolutionPath()
            self._num_states = self._path.getStateCount()
            self.__next_idx = 1
            return True
        else:
            return False

            # p = self._setup.getSolutionPath()
            # ps = og.PathSimplifier(self._setup.getSpaceInformation())
            # ps.simplifyMax(p)
            # ps.smoothBSpline(p)
            # print(self._path)


    def isStateValid(self, state):
        x = float(state[0])
        y = float(state[1])
        # print('x,y:',x,y)
        state_position = coord.Coord(x, y)
        return not self._map_manager.get_map().check_obstacle_collision(state_position, False)

