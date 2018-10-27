import re
import os
import glob
import sensors
from importlib import import_module

# TODO: could this all be a static class?
class Sensors(object):
    def __init__(self):
        self._slist = {}
        self._gdir = map(lambda x: re.search('.*\/(rpjios\/.*)', x).group(1), glob.glob(os.path.split(__file__)[0] + '/sensors/*.py'))
        for mn in map(lambda x: x.replace('/', '.').replace('.py', ''), self._gdir): 
            if not ('init' in mn or 'Base' in mn):
                self._slist[mn.replace('rpjios.sensors.','')] = import_module(mn)

    def list(self):
        return self._slist.keys()

    def create(self, name, config=None, redis_cfg=None):
        cf = self._slist[name].Factory
        if redis_cfg:
            if not config:
                config = {}
            config['redis_cfg'] = redis_cfg
        return cf(**config) if config else cf()
