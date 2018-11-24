from rpjios.SensorBase import Sensor
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008 as MCP

class Analog(Sensor):
    def __init__(self, port=0, device=0, bitwidth=10, adc_input=None, debounce=3, *args, **kwargs):
        if adc_input is None or adc_input < 0 or adc_input > 7:
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
