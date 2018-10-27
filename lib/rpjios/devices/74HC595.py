import RPi.GPIO as gpio
import Queue
import threading
from time import sleep

class ShiftReg595(object):
    DEFAULT_PULSE_DURATION = 0.00001
    DEFAULT_MSB_FIRST = False
    DEFAULT_PIN_NUMBERING = gpio.BCM

    def __init__(self, SER=None, RCLK=None, SRCLK=None, 
            msb_first=DEFAULT_MSB_FIRST, pulse_dir=DEFAULT_PULSE_DURATION,
            pin_numbering=DEFAULT_PIN_NUMBERING):
        if not (SER and RCLK and SRCLK):
            raise BaseException("Bad arguments (SER={} RCLK={} SRCLK={}"
                    .format(SER, RCLK, SRCLK))
        self._msbf = msb_first
        self._pd = pulse_dir
        self._pinno = pin_numbering
        self._pins = [
                [SER, gpio.OUT, gpio.LOW], 
                [SRCLK, gpio.OUT, gpio.LOW],
                [RCLK, gpio.OUT, gpio.LOW]
                ]
        self._b = 0
        self._setup()

    def __del__(self):
        self._cleanup()

    def _setup(self):
        gpio.setmode(self._pinno)
        gpio.setwarnings(True)
        for pin in self._pins:
            gpio.setup(pin[0], pin[1], initial=pin[2])

    def _cleanup(self):
        gpio.cleanup()

    def _pulse(self, pin):
        gpio.output(pin, 1)
        sleep(self._pd)
        gpio.output(pin, 0)

    def _send(self):
        for i in range(8):
            val = (self._b >> (i if self._msbf else (7-i))) & 0x1
            gpio.output(self._pins[0][0], val)
            self._pulse(self._pins[1][0])
        self._pulse(self._pins[2][0])

    @property
    def value(self):
        return self._b

    @value.setter
    def value(self, b):
        self._b = b
        self._send()

if __name__ == "__main__":
    sr = ShiftReg595(SER=5, RCLK=6, SRCLK=13)
    for i in range(256):
        sr.value = i
        sleep(abs(0.04-(0.0001*i)))    
    sr.value = 0
