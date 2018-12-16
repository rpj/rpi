from rpjios.devices.SPS30 import SPS30
from rpjios.SensorBase import Sensor, SensorName, SensorDesc

class Factory(Sensor):
    @SensorName("SPS30")
    @SensorDesc("Sensiron SPS30 particulate matter sensor")
    def __init__(self, *args, **kwargs):
        if 'frequency' in kwargs and int(kwargs['frequency']) > 1:
            raise BaseException("SPS30 only supports frequencies of 1Hz or less")
        super(Factory, self).__init__(*args, **kwargs)
        self._sps = SPS30(**kwargs)
        self._meta['serial_number'] = self._sps.serial_number
        self._meta['driver_version'] = self._sps.driver_version

    def _runloop(self):
        meas = self._sps.measurement
        if meas is not None:
            self.publish(self._attrs_to_dict(meas))
