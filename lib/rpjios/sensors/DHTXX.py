from Base import Sensor, SensorName, SensorDesc
import Adafruit_DHT as dht

class Factory(Sensor):
    @SensorName("DHTXX")
    @SensorDesc("DHTXX (11/22) ambient temperature and humidity 1-wire sensor")
    def __init__(self, data_pin=None, variant=None, *args, **kwargs):
        if not data_pin:
            raise BaseException("Must define a data pin for DHTXX sensor!")
        if not variant:
            raise BaseException("Must define a variant of DHTXX sensor!")
        if not (variant == 11 or variant == 22):
            raise BaseException("Unrecognized DHTXX variant '{}'!".format(variant))
        super(Factory, self).__init__(*args, **kwargs)
        self._meta['dht_config'] = {'pin': data_pin, 'variant': variant}
        self._pin = data_pin
        self._var = dht.DHT11 if variant == 1 else dht.DHT22 

    def _runloop(self):
        h, t = dht.read_retry(self._var, self._pin)
        if h and t:
            self.publish({'tempF': (t*9/5.0+32), 'humidity%': h})
