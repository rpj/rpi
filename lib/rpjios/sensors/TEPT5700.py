from Base import SensorName, SensorDesc
from AnalogBase import Analog

class Factory(Analog):
    @SensorName("TEPT5700")
    @SensorDesc("TEPT5700 ambient light sensor (analog)")
    def __init__(self, *args, **kwargs):
        super(Factory, self).__init__(*args, **kwargs)

    def _runloop(self):
        self.publish(self.raw_value)
