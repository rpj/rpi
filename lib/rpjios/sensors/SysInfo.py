import os
import psutil
from datetime import timedelta
from Base import Sensor, SensorName, SensorDesc

def cpuTemp():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        return (float(f.read()) / 1000.0) * 1.8 + 32

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = int(float(f.readline().split()[0]))
        uptime_string = str(timedelta(seconds = uptime_seconds))
        if (uptime_seconds < 10*60*60):
            uptime_string = '0'+uptime_string
    return uptime_string

class Factory(Sensor):
    @SensorName("SysInfo")
    @SensorDesc("Local system information")
    def __init__(self, *args, **kwargs):
        if 'frequency' not in kwargs:
            kwargs['frequency'] = 2
        super(Factory, self).__init__(*args, **kwargs)
        self._hn = None
        with open('/etc/hostname') as f:
            self._hn = f.read().strip()

    def _runloop(self):
        _st = os.statvfs('/')
        self.publish({
            'cpu%': psutil.cpu_percent(), 
            'cpuF': cpuTemp(), 
            'vm%': psutil.virtual_memory().percent,
            'fsFree%': {
                '/': (float(_st.f_bfree) / float(_st.f_blocks)) * 100.0
            },
            'uptime': uptime(),
            'hostname': self._hn
        })
