import pyglet
import gamemap
import graphics
import agent
import action

class Replay(object):

	def __init__(self, replay_file, fps, velocity, fixed_time_quanta):

		self.__rf = open(replay_file, 'r')
		self.__map_id = None
		self.__num_hiders = None
		self.__num_seekers = None

		while True: 
			token = self.__rf.readline().strip()
			if token == 'simulation:':
				break
			pre_token = token.split(':')[0]
			post_token = token.split(':')[1]

			if pre_token == 'map_id':
				self.__map_id = int(post_token)
			elif pre_token == 'num_hiders':
				self.__num_hiders = int(post_token)
			elif pre_token == 'num_seekers':
				self.__num_seekers = int(post_token)
			else:
				print('PARSING FAILED')

		print('map_id:', self.__map_id)
		print('num_hiders:', self.__num_hiders)
		print('num_seekers:', self.__num_seekers)

		self.__map = gamemap.PolygonMap(self.__map_id)
		window_width = self.__map.get_map_width()
		window_height = self.__map.get_map_height()

		self.__fps = fps
		self.__velocity = velocity
		self.__fixed_time_quanta = fixed_time_quanta

		self.__inactive_hiders = []
		self.__first_flag = {agent.AgentType.Hider:True, agent.AgentType.Seeker:True}


		self.__window = graphics.Graphics(window_width, window_height, self.__num_hiders, self.__num_seekers, False, None, fps, velocity, self.__map, fixed_time_quanta)
		print('graphics class initialized')


	def __update_agents(self, agent_type, agent_data):
		agent_list = agent_data.split(';')
		if agent_type == agent.AgentType.Hider:
			num_agents = self.__num_hiders
		elif agent_type == agent.AgentType.Seeker:
			num_agents = self.__num_seekers
		for i in range(num_agents):
			# print('idx:',i)
			if agent_type == agent.AgentType.Hider:
				if i in self.__inactive_hiders:
					continue
			solo_agent = agent_list[i].strip()
			if solo_agent == 'X*X':
				print('setting hider inactive')
				self.__window.set_player_inactive(agent_type, i)
				self.__inactive_hiders.append(i)
			else:
				solo_agent = solo_agent.split('*')
				position = solo_agent[0].split(',')
				print('position:', position)
				print('hiders caught:', len(self.__inactive_hiders))
				x = int(float(position[0]))
				y = int(float(position[1]))
				act = action.Action.string2action[position[2]]
				print('act:', act)
				if act != action.Action.ST:
					rotation = action.ROTATION[act]
					if not self.__first_flag[agent_type]:
						self.__window.set_player_rotation_raw(agent_type, i, rotation)


				
				self.__window.set_player_position_raw(agent_type, i, x, y)
				visibility_list = solo_agent[1].split(',')
				visibility_list = [int(num) for num in visibility_list]
				visibility_tuple = tuple(visibility_list)
				self.__window.set_player_visibility_polygon_raw(agent_type,i,visibility_tuple)


	def update(self, dt):

		if len(self.__inactive_hiders) != self.__num_hiders:
			hider_data = self.__rf.readline()
			self.__update_agents(agent.AgentType.Hider, hider_data)
			self.__first_flag[agent.AgentType.Hider] = False

			seeker_data = self.__rf.readline()
			self.__update_agents(agent.AgentType.Seeker, seeker_data)
			self.__first_flag[agent.AgentType.Seeker] = False
		else:
			pyglet.app.exit()


	def run_replay(self):
		pyglet.clock.schedule_interval(self.update, 1/30.0) # update at 60Hz
		pyglet.app.run()
