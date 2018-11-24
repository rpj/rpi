import redis
import json
import time
import threading
import uuid
import functools
from monotonic import time as mt
from rpjios import Util
from rpjios.Types import Message, Constants
from rpjios.SubscriberBase import Subscriber, PSubscriber

def SensorName(sname):
    def SensorName_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['name'] = sname
            func(*args, **kwargs)
        return wrapper
    return SensorName_decorator

def SensorDesc(sdesc):
    def SensorDesc_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['desc'] = sdesc
            func(*args, **kwargs)
        return wrapper
    return SensorDesc_decorator

def SensorCategory(sCategory):
    def SensorCategory_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['category'] = sCategory
            func(*args, **kwargs)
        return wrapper
    return SensorCategory_decorator


class SensorException(BaseException):
    pass

class Sensor(object):
    def __init__(self, name=None, frequency=None, desc=None, category='sensor', redis_cfg={}, *args, **kwargs):
        self._meta = {}
        self._name = name
        self._name_add = None if 'name_append' not in kwargs else kwargs['name_append']
        self._meta['location'] = self._location = None if 'location' not in kwargs else kwargs['location']
        self._meta['hostname'] = Util.hostname()
        self.channel = Constants.NAMESPACE_SEP.join([self._meta['hostname'], category, self.name])
        self._meta['description'] = self.desc = desc
        self.freq = frequency
        if self.freq is not None:
            self._lasttick = 0
            self._sleeptime = 1.0 / float(self.freq)
        self._run = True
        self._redis = redis.StrictRedis(**redis_cfg)
        self._sub = Subscriber(channel=self.channel)
        if 'meta' in kwargs:
            self._meta['config_meta'] = kwargs['meta']

    @property
    def name(self):
        return "{}{}".format(self._name, self._name_add if self._name_add else "")

    @property
    def type(self):
        return self._name

    def __str__(self):
        return "<{} '{}{}' type={} channel={}>".format(__name__, self.name,
                " at {}".format(self._location) if self._location else "", 
                self.type, self.channel) 

    def _attrs_to_dict(self, objfrom):
        ret = {}
        for n in dir(objfrom):
            if not n.startswith('_'):
                ga = getattr(objfrom, n)
                if not callable(ga):
                    ret[n] = ga
        return ret

    def _tickloop(self):
        while (self._run):
            n = mt.time()
            if n - self._lasttick > self._sleeptime:
                self._lasttick = n
                self._runloop()
            time.sleep(0.01)

    def _setup(self):
        pass

    def _cleanup(self):
        pass

    def start(self):
        try:
            self._setup()
            msg = {'description': self.desc, 'meta': self._meta}
            self.publish(msg, Message.SETUP_DONE)
            t = self._runloop if self.freq is None else self._tickloop
            self._thread = threading.Thread(target=t)
            self._thread.daemon = True
            self._thread.start()
        except SensorException as se:
            print "Failed setup: {}".format(se)

    def stop(self):
        self._run = False
        del self._sub
        self._cleanup()
        self._thread.join()
        self.publish(mtype=Message.SENSOR_GONE)
        print "{} stopped".format(self)

    def subscribe_to(self, subfunc):
        self._sub.add_listener(subfunc)

    def publish(self, value=None, mtype=Message.GENERAL):
        m = {
                'type': mtype, 
                'source': self.channel, 
                'ts': mt.time()
            }

        if self._location:
            m['location'] = self._location
        if value is not None:
            try:
                m['value'] = json.loads(value)
            except:
                m['value'] = value

        self._redis.publish(self.channel, json.dumps(m))

    def metadata(self):
        m = {
                'name': self.name, 
                'channel': self.channel, 
                'description': self.desc,
            }

        if self.freq is not None:
            m['frequency'] = "{}Hz".format(self.freq)

        for k in self._meta:
            m[k] = self._meta[k]

        return m

    def id(self):
        return self.channel
