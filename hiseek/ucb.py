import math
import time

import numpy as np

class UCB(object):

	def __init__(self, num_actions, alpha=0.1):
		'''
			u_cap[i] : Mean emprirical reward associated with each strategic point
			N[i]: #Time strategic point i has been choosen
			t: #Total number of time steps/#Total number of choices made
			UCB[i]: Upper Confidence Bound associated with each strategic point
		'''
		np.random.seed(int(time.time()))
		self.__num_actions = num_actions
		self.__u_cap = [0 for i in range(self.__num_actions)]
		self.__N = [1 for i in range(self.__num_actions)]
		self.__t = 1
		self.__UCB = [0 for i in range(self.__num_actions)]
		self.__alpha = alpha

	def set_initial_average(self, action, average):
		if self.__N[action] == 1:
			self.__u_cap[action] = average

	def set_initial_bounds(self):
		flag = True
		for i in range(self.__num_actions):
			if self.__N[i] != 1:
				flag = False
				break
		if flag:
			self.__t = self.__num_actions
			self.__update_ucb()

	def get_greatest_actions(self, num_actions=1, consideration=None):
		'''
			consideration: List of actions which should be considered during maximum UCB selection
							, if None, all the actions are considered
		'''
		considered_actions = []
		# print('UCB:', self.__UCB)
		if consideration != None:
			considered_actions = consideration
		else:
			considered_actions = range(self.__num_actions)
		greatest_arms = sorted(considered_actions, key=lambda k: self.__UCB[k], reverse=True)
		greatest_arms = greatest_arms[0:num_actions]
		return greatest_arms

	def select_action(self, consideration = None):

		# self.__t += 1
		# print('UCB:', self.__UCB)
		actions =  np.argwhere(self.__UCB == np.amax(self.__UCB))
		actions = actions.flatten()
		# print('Max actions:', actions)
		action = np.random.choice(actions)
		# print('Action picked:', action)
		return action

	def update(self, action, reward, printUcb=False):
		self.__update_ucb_params(action, reward)
		self.__update_ucb(printUcb)

		
	def __update_ucb_params(self, action, reward):
		# print('Updating for strategic point:', action)
		# if reward < 0:
			# print('Updating with a negative reward:', reward)
		self.__u_cap[action] = self.__u_cap[action] + (reward - self.__u_cap[action])*1.0/(self.__N[action] + 1)
		self.__N[action] += 1 

	def __update_ucb(self, printUcb=False):
		# print('After update:')
		self.__t += 1
		for i in range(self.__num_actions):
			self.__UCB[i] = self.__u_cap[i] + math.sqrt(self.__alpha * math.log(self.__t)/(2*self.__N[i]))
			if printUcb:
				print(i, self.__UCB[i])

	def __str__(self):
		return str(self.__UCB)

