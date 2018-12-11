import smbus2
import bme280
import time
from datetime import datetime
from rpjios.SensorBase import Sensor, SensorName, SensorDesc

I2C_PORT_DEFAULT = 1
I2C_ADDRESS_DEFAULT = 0x76

class Factory(Sensor):
    @SensorName("BME280")
    @SensorDesc("Bosch I2C low power pressure, temperature & humidity sensor")
    def __init__(self, i2c_port=I2C_PORT_DEFAULT, i2c_address=I2C_ADDRESS_DEFAULT, *args, **kwargs):
        if i2c_port is None or i2c_port < 0 or i2c_address is None or i2c_address < 0:
            raise BaseException("Bad I2C port or address for BME280 specification")
        super(Factory, self).__init__(*args, **kwargs)
        self._port = i2c_port
        self._addr = i2c_address

    def _setup(self):
        self._bus = smbus2.SMBus(self._port)
        self._meta['calibration_data'] = self._cbdata = bme280.load_calibration_params(self._bus, self._addr)

    def _runloop(self):
        data = self._attrs_to_dict(bme280.sample(self._bus, self._addr, self._cbdata))
        if 'temperature' in data:
            data['temperature'] = (data['temperature'] * 1.8) + 32.0
        if 'timestamp' in data and type(data['timestamp']) == datetime:
            data['timestamp'] = time.mktime(data['timestamp'].timetuple())
        if 'id' in data:
            del data['id']
        if 'uncompensated' in data:
            del data['uncompensated']
        self.publish(data)

