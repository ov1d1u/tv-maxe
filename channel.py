class Channel:
	def __init__(self, **args):
		self.id = args['id']
		self.icon = args['icon']
		self.name = args['name']
		self.streamurls = args['streamurls']
		self.source = args['source']
		self.params = 'params' in args and args['params'] or {}
		self.guide = 'guide' in args and args['guide'] or ''
		self.audiochannels = 'audiochannels' in args and args['audiochannels'] or []
		self.liststore = args['liststore']
		self.info = 'info' in args and args['info'] or {'name' : 'Unknown',
								'epgurl' : '',
								'version' : '0.00',
								'author' : '',
								'url' : 'http://www.pymaxe.com'}

	def get_iter(self, col = 0):
		iter = self.liststore.get_iter_root()
		while iter:
			cid = self.liststore.get_value(iter, col) # current id
			if self.id == cid:
				return iter
			iter = self.liststore.iter_next(iter)
		return None
		
