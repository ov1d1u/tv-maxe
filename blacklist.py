import sqlite3, os

class Blacklist:
	def __init__(self):
		self.conn = sqlite3.connect(os.getenv('HOME') + '/.tvmaxe/blacklist.db')
		self.conn.row_factory = sqlite3.Row
		self.conn.text_factory = str
		self.data = self.conn.cursor()
		self.data.execute("CREATE TABLE IF NOT EXISTS blacklist (id, name)")
		self.conn.commit()
		self.gui = None

	def add(self, channel):
		id = channel.id
		name = channel.name
		self.data.execute("INSERT INTO blacklist VALUES (?, ?)", [id, name])
		self.conn.commit()
		
	def is_blacklisted(self, channel):
		ret = False
		self.data.execute("SELECT * FROM blacklist")
		for x in self.data:
			if x['id'] == channel.id:
				ret = True
		return ret
		
	def showGUI(self, gui):
		self.gui = gui
		blackstore = self.gui.get_object('blackstore')
		blackstore.clear()
		self.data.execute("SELECT * FROM blacklist")
		for x in self.data:
			id = x['id']
			name = x['name']
			blackstore.append([id, name])
		self.gui.get_object('window14').show()
		
	def hideGUI(self):
		self.gui.get_object('window14').hide()
		
	def remove(self):
		blacktree = self.gui.get_object('treeview5')
		blackstore = self.gui.get_object('blackstore')
		treeselection = blacktree.get_selection()
		(model, iter) = treeselection.get_selected()
		if not iter:
			return
		id = model.get_value(iter, 0)
		self.data.execute("DELETE FROM blacklist WHERE id=?", (id, ))
		model.remove(iter)
		self.conn.commit()
		return id
		
	def clear(self):
		ret = []
		model = self.gui.get_object('blackstore')
		self.data.execute("DELETE FROM blacklist")
		self.conn.commit()
		iter = model.get_iter_root()
		while iter:
			id = model.get_value(iter, 0)
			ret.append(id)
			iter = model.iter_next(iter)
		model.clear()
		return ret