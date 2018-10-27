import bme680
import sys
from time import sleep
from Base import Sensor, SensorName, SensorDesc

class Factory(Sensor):
    @SensorName("BME680")
    @SensorDesc("Bosch low power gas, pressure, temperature & humidity sensor")
    def __init__(self, *args, **kwargs):
        super(Factory, self).__init__(*args, **kwargs)

    def _setup(self):
        try:
            self._sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        except IOError:
            self._sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

        if self._sensor is None:
            raise Base.SensorException("No BME680 I2C sensor found") 

        self._meta['calibration_data'] = {}
        cd = self._attrs_to_dict(self._sensor.calibration_data)
        for k in cd:
            if not callable(cd[k]):
                self._meta['calibration_data'][k] = cd[k]

        # TODO: MAKE CONFIG'ABLE
        self._sensor.set_humidity_oversample(bme680.OS_2X)
        self._sensor.set_pressure_oversample(bme680.OS_4X)
        self._sensor.set_temperature_oversample(bme680.OS_8X)
        self._sensor.set_filter(bme680.FILTER_SIZE_3)
        self._sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

        # TODO: SAME. ALSO MAKE PROFILES SELECTABLE AND WHAT NOT
        self._sensor.set_gas_heater_temperature(320)
        self._sensor.set_gas_heater_duration(150)
        self._sensor.select_gas_heater_profile(0)

        self._meta['initial_reading'] = self._attrs_to_dict(self._sensor.data)

    def _runloop(self):
        while (self._run):
            if self._sensor.get_sensor_data():
                data = self._attrs_to_dict(self._sensor.data)
                if 'temperature' in data:
                    data['temperature'] = data['temperature'] * 1.8 + 32
                self.publish(data)
            sleep(1.0)
