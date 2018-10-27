from Base import Analog, SensorName, SensorDesc

class Factory(Analog):
    @SensorName("Soil")
    @SensorDesc("Soil moisture sensor")
    def __init__(self, *args, **kwargs):
        super(Factory, self).__init__(*args, **kwargs)

    def _runloop(self):
        self.publish(self.raw_value)
