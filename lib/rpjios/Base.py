import redis
import uuid

#TODO: move sensor base stuff here!! (and have it use Redis base!)
#also TODO: sensor classes should be strictly restricted to only emitting to a local redis (maybe?)

class Redis(object):
    def __init__(self, *args, **kwargs):
        self._r = redis.StrictRedis(**kwargs)
        self._p = self._r.pubsub()
        self._uuid = uuid.uuid4()

    def __str__(self):
        return "<Base.Redis {} _r={}>".format(self._uuid, self._r)
