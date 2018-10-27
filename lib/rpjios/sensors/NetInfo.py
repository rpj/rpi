import re
import os
import psutil
from Base import Sensor, SensorName, SensorDesc
from subprocess import Popen, PIPE

class Factory(Sensor):
    @SensorName("NetInfo")
    @SensorDesc("Network information")
    def __init__(self, *args, **kwargs):
        super(Factory, self).__init__(*args, **kwargs)
        self._last = {}

    def _gather_wifi(self, iface):
        c = ['/sbin/iwgetid', iface, '--raw']
        g = { 'ssid': None, 'mac': '--ap', 'freq': '--freq', 'chan': '--channel' }
        for gk in g:
            ta = list(c)
            if g[gk] is not None:
                ta.append(g[gk])
            g[gk] = Popen(ta, stdout=PIPE).communicate()[0].strip()
            if gk == 'freq':
                g[gk] = "{0:.2f} GHz".format(float(g[gk]) / 1e9)
        c2 = ["Bit Rate", "Tx-Power", "Link Quality", "Signal level"]
        c2d = {}
        for cl in Popen(['/sbin/iwconfig', iface], stdout=PIPE).communicate()[0].split('\n'):
            for c2i in c2:
                m = re.match(".*{}\=(.*?)(?:\s\s)+".format(c2i), cl)
                if m and len(m.groups()):
                    c2d[c2i] = m.groups()[0]
        if len(c2d):
            g['extended_info'] = c2d
        return g

    def _runloop(self):
        cur = {}
        cur['internet_reachable'] = True if os.system("/usr/bin/curl http://google.com > /dev/null 2>&1") == 0 else False
        cur['interfaces'] = {}

        ni = psutil.net_if_addrs()
        for n in ni:
            if n != 'lo' and len(ni[n]):
                cur['interfaces'][n] = {'addr': ni[n][0].address}
                if 'wlan' in n:
                    wf = self._gather_wifi(n)
                    for k in wf:
                        cur['interfaces'][n][k] = wf[k]

        dirty = False
        for k in cur:
            if k not in self._last or self._last[k] != cur[k]:
                dirty = True
                break
        
        if 1:#dirty:
            self.publish(cur)

        self._last = cur

