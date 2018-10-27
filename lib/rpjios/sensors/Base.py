import redis
import json
import time
import threading
import uuid
import functools
import Queue
from monotonic import time as mt

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

class SensorException(BaseException):
    pass

class Message(object):
    SETUP_DONE = "AVAILABLE"
    GENERAL = "VALUE"
    SENSOR_GONE = "GONE"

# This class will always prepend the channel given with Sensor.CHANNEL,
# so as not to be a generic subscriber but instead scoped to
# this "Sensor" namespace
class Subscriber(object):
    @staticmethod
    def channels():
        return redis.StrictRedis().execute_command("PUBSUB", "CHANNELS", "{}*".format(Sensor.CHANNEL))

    def __init__(self, channel=None, mtype_filter=None):
        if channel is None:
            raise BaseException("No channel name given!")

        self._subs = []
        self._q = Queue.Queue()
        self._pubsub = redis.StrictRedis().pubsub()
        self._pssubfunc = self._pubsub.subscribe
        self._psunsubfunc = self._pubsub.unsubscribe
        self._chan = "{}.{}".format(Sensor.CHANNEL, channel)
        self._filter = ['psubscribe', 'subscribe']
        if isinstance(mtype_filter, list):
            self._filter.extend(mtype_filter)
        self._listen = None
        self._run = False
        self._issetup = False

    def __str__(self):
        return "<{} channel='{}'>".format(self.__class__.__name__, self._chan)
        
    def __del__(self):
        self._run = False
        self._psunsubfunc()
        if self._listen:
            self._listen.join()

    def _setup(self):
        self._listen = threading.Thread(target=self._sub_thread)
        self._listen.daemon = True
        self._pssubfunc(self._chan)
        self._run = True
        self._listen.start()

    def _sub_thread(self):
        while self._run:
            for m in self._pubsub.listen():
                if self._filter and m['type'] in self._filter:
                    continue

                if len(self._subs):
                    map(lambda sf: sf(m), self._subs)
                else:
                    self._q.put(m)

    # if no listeners have been added, blocks until a message is available and returns it
    # otherwise, returns None without blocking
    def get_message(self):
        if not self._issetup:
            self._setup()
        return None if len(self._subs) else self._q.get()

    # once a listener has been added, any messages left in the queue will be drained
    # to the registered listener and thereafter .get_message() will always return None
    def add_listener(self, listener):
        if not self._issetup:
            self._setup()

        if not self._q.empty():
            try:
                for m in self._q.get_nowait():
                    listener(m)
            except Empty:
                pass

        self._subs.append(listener)

    def add_subscriber(self, l):
        return self.add_listener(l)

# This class will always prepend the pattern given with Sensor.CHANNEL,
# so as not to be a generic pattern subscriber but instead scoped to
# this "Sensor" namespace
class PSubscriber(Subscriber):
    def __init__(self, *args, **kwargs):
        super(PSubscriber, self).__init__(*args, **kwargs)
        self._pssubfunc = self._pubsub.psubscribe
        self._psunsubfunc = self._pubsub.punsubscribe

class Sensor(object):
    CHANNEL = 'rpjios.sensors'

    def __init__(self, name=None, frequency=None, desc=None, redis_cfg={}, *args, **kwargs):
        self._meta = {}
        self._name = name
        self._name_add = None if 'name_append' not in kwargs else kwargs['name_append']
        self._meta['location'] = self._location = None if 'location' not in kwargs else kwargs['location']
        self.uuid = uuid.uuid4()
        self.channel = "{}.{}.{}".format(self.CHANNEL, self.name, str(self.uuid))
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
            msg = {'id':str(self.uuid), 'description':self.desc,'meta':self._meta}
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
                'source': self.name, 
                'id': str(self.uuid), 
                'ts': mt.time()
            }

        if self._location:
            m['location'] = self._location
        if value:
            try:
                m['value'] = json.loads(value)
            except:
                m['value'] = value

        self._redis.publish(self.channel, json.dumps(m))

    def metadata(self):
        m = {
                'name': self.name, 
                'channel': self.channel, 
                'id': str(self.uuid), 
                'description': self.desc,
            }

        if self.freq is not None:
            m['frequency'] = "{}Hz".format(self.freq)

        for k in self._meta:
            m[k] = self._meta[k]

        #m['raw_attrs'] = self._attrs_to_dict(self)

        return m

    def id(self):
        return str(self.uuid)

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008 as MCP

class Analog(Sensor):
    def __init__(self, port=0, device=0, bitwidth=10, adc_input=None, debounce=3, *args, **kwargs):
        if not adc_input:
            raise SensorException("Unspecified ADC input number for {}".format(self))
        super(Analog, self).__init__(*args, **kwargs)
        self.bitwidth = bitwidth
        self._db = debounce
        self._meta['adc_cfg'] = {'port':port,'dev':device,'bw':bitwidth,'chan':adc_input,'debounce':self._db}
        self._mcp = MCP.MCP3008(spi=SPI.SpiDev(port, device)) 
        self._read = lambda: self._mcp.read_adc(adc_input)

    @property
    def raw_value(self):
        if self._db > 1:
            db = 0.0
            for _ in range(self._db):
                db += float(self._read())
            return db / float(self._db)
        else:
            return float(self._read())
