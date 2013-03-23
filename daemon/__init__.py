from daemon import Daemon
import inspect, os, subprocess, sys

class TDaemon:
	def __init__(self, tvmaxe):
		"""tvmaxe = path of tvmaxe script"""
		self.path = os.path.split(os.path.abspath(__file__))[0] + 'tvmaxed.py'
		self.python = sys.executable
		self.tvmaxepy = tvmaxe

	def start(self):
		p = subprocess.Popen([self.python, self.path, self.tvmaxepy, 'start'])
	
	def stop(self):
		p = subprocess.Popen([self.python, self.path, self.tvmaxepy, 'stop'])
		
	def restart(self):
		p = subprocess.Popen([self.python, self.path, self.tvmaxepy, 'restart'])
