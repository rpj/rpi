from rpjios.SensorBase import SensorName, SensorDesc
from rpjios.AnalogBase import Analog

class Factory(Analog):
    @SensorName("LM335")
    @SensorDesc("LM335 precision temperature sensor (analog)")
    def __init__(self, voltage=3.3, *args, **kwargs):
        super(Factory, self).__init__(*args, **kwargs)
        self._vconv = lambda x: (((x / 2 ** self.bitwidth)*(voltage * 10.0)) - 273.15) * 1.8 + 32
        if voltage == 3.3:
            self._vconv = lambda x: x * 0.580078125 - 459.67

    def _runloop(self):
        self.publish(self._vconv(self.raw_value))
