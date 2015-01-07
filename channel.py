class Channel:
    def __init__(self, *args, **kwargs):
        self.id = kwargs['id']
        self.icon = kwargs['icon']
        self.name = kwargs['name']
        self.streamurls = kwargs['streamurls']
        self.source = kwargs['source']
        self.params = 'params' in kwargs and kwargs['params'] or {}
        self.guide = 'guide' in kwargs and kwargs['guide'] or ''
        self.audiochannels = 'audiochannels' in kwargs and kwargs['audiochannels'] or []
        self.liststore = kwargs['liststore']
        self.info = 'info' in kwargs and kwargs['info'] or {'name' : 'Unknown',
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
        
