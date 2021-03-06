import redis
import uuid
import Util

#TODO: move sensor base stuff here!! (and have it use Redis base!)
#also TODO: sensor classes should be strictly restricted to only emitting to a local redis (maybe?)

class Redis(object):
    def __init__(self, *args, **kwargs):
        if 'host' not in kwargs:
            kwargs = Util.cur_redis_dict()
        self._r = redis.StrictRedis(**kwargs)
        self._p = self._r.pubsub()
        self._uuid = uuid.uuid4()

    def __str__(self):
        return "<Base.Redis {} _r={}>".format(self._uuid, self._r)
