import Queue
import redis
import json
import threading
import Types
import RedisBase

class Subscriber(RedisBase.Redis):
    @staticmethod
    def channels():
        return redis.StrictRedis().execute_command("PUBSUB", "CHANNELS", "{}*".format(Sensor.CHANNEL))

    def __init__(self, channel, mtype_filter=None, *args, **kwargs):
        if channel is None:
            raise BaseException("No channel name given!")

        super(Subscriber, self).__init__(*args, **kwargs)
        self._subs = []
        self._q = Queue.Queue()
        self._pubsub = self._r.pubsub()
        self._pssubfunc = self._pubsub.subscribe
        self._psunsubfunc = self._pubsub.unsubscribe
        self._chan = channel
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
