class Message(object):
	'''
		Message class to encapsulate the message which is sent across agents
	'''
	def __init__(self, sender, receiver, content):
		self.__sender = sender
		self.__receiver = receiver
		self.__content = content

	def get_sender(self):
		return self.__sender

	def get_receiver(self):
		return self.__receiver

	def get_content(self):
		return self.__content


class AgentMessenger(object):
	'''
		AgentMessenger facilitates an agent to manage as well as send and receive its messages
	'''
	def __init__(self, agent_id, team_messenger):
		self.__team_messenger = team_messenger
		self.__id = agent_id
		self.__inbox = []
		self.__outbox = []

	def compose(self, receiver, content):
		message = Message(self.__id, receiver, content)
		self.__team_messenger.send(message)
		self.__outbox.append((False, message))

	def receive(self, message):
		self.__inbox.append((False, message))

	def get_new_messages(self):
		unread_messages = []
		for i in reversed(self.__inbox):
			message = self.__inbox[i]
			if not message[0]:
				message[0] = True
				unread_messages.append(message[1])
		return unread_messages

	def broadcast(self, content):
		agent_ids = self.__team_messenger.get_all_ids()
		for agent_id in agent_ids:
			if agent_id != self.__id:
				self.compose(agent_id, content)

class TeamMessenger(object):
	'''
		TeamMessenger facilitates AgenMessagemessenger to communicate with each other
		by allowing them to send and receive messages to/from other agents.
	'''

	def __init__(self):
		self.__agent_messengers = {}

	def create_agent_messenger(self, agent_id):
		agent_messenger = AgentMessenger(agent_id, self)
		self.__agent_messengers[agent_id] = agent_messenger
		return agent_messenger

	def send(self, message):
		receiver_id = message.get_receiver()
		assert(receiver_id in self.__agent_messengers)
		receiver_messenger = self.__agent_messengers[receiver_id]
		receiver_messenger.receive(message)

	def get_all_ids(self):
		return self.__agent_messengers.keys()



