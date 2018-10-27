from Base import Sensor, SensorName, SensorDesc

class Factory(Sensor):
    @SensorName("DS18S20")
    @SensorDesc("Digital 1-wire ambient temperature sensor")
    def __init__(self, devpath=None, *args, **kwargs):
        if not devpath:
            raise BaseException("Bad args for {}".format(name))
        super(Factory, self).__init__(*args, **kwargs)
        self._meta['value_unit'] = 'F'
        self._meta['devpath'] = self._devpath = devpath

    def _runloop(self):
        with open(self._devpath) as f:
            lines = f.read().split('\n')
            if len(lines) > 1:
                v = lines[1].split(' ')[-1].split('=')[1]
                self.publish(int((((float(v) / 1000.0) * 1.8) + 32))) 
