import math

import numpy as np

class UCB(object):

	def __init__(self, num_actions, alpha=0.1):
		'''
			u_cap[i] : Mean emprirical reward associated with each strategic point
			N[i]: #Time strategic point i has been choosen
			t: #Total number of time steps/#Total number of choices made
			UCB[i]: Upper Confidence Bound associated with each strategic point
		'''
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


	def select_action(self):
		self.__t += 1
		action =  np.argmax(self.__UCB)
		return action

	def update(self, action, reward):
		self.__update_ucb_params(action, reward)
		self.__update_ucb()
		
	def __update_ucb_params(self, action, reward):
		# print('Updating for strategic point:', action)
		if reward < 0:
			print('Updating with a negative reward:', reward)
		self.__u_cap[action] = self.__u_cap[action] + (reward - self.__u_cap[action])*1.0/(self.__N[action] + 1)
		self.__N[action] += 1 

	def __update_ucb(self):
		# print('After update:')
		for i in range(self.__num_actions):
			self.__UCB[i] = self.__u_cap[i] + math.sqrt(self.__alpha * math.log(self.__t)/(2*self.__N[i]))
			# print(i, self.__UCB[i])

	def __str__(self):
		return str(self.__UCB)

