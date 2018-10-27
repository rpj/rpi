from __future__ import print_function
import re
import os
import sys
import psutil
from datetime import timedelta
from subprocess import Popen, PIPE

DEBUG_LEVEL_LOWEST = 0
DEFAULT_DEBUG_LEVEL = 1

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def dprint(*args, **kwargs):
    _dlvl = os.environ['DEBUG'] if 'DEBUG' in os.environ else 0
    _clvl = DEFAULT_DEBUG_LEVEL

    if 'level' in kwargs:
        _clvl = kwargs['level']
        del kwargs['level']

    if int(_dlvl) >= int(_clvl):
        eprint(*args, **kwargs)

def parse_redis_url(url_str):
    url_re = re.compile(r"redis\:\/\/(?:(?:(.*?)\:)?(.*?)\@)?([a-zA-Z\d\-_\.]+)(?:\:(\d+))?")
    m = url_re.match(url_str)
    if m and len(m.groups()) == 4:
        g = m.groups()
        rvt = { 'password': g[1] if g[0] else None, 'host': g[2], 'port': g[3] }
        rv = {}
        for k in rvt:
            if rvt[k]:
                rv[k] = rvt[k]
        return rv

def cur_redis_dict():
    return parse_redis_url(os.environ['REDIS_URL'])

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = int(float(f.readline().split()[0]))
        uptime_string = str(timedelta(seconds = uptime_seconds))
        if (uptime_seconds < 10*60*60):
            uptime_string = '0'+uptime_string
    return uptime_string

def _gather_wifi(iface):
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

def network_ifaces():
    rv = {}
    ni = psutil.net_if_addrs()
    for n in ni:
        if n != 'lo' and len(ni[n]):
            rv[n] = {'addr': ni[n][0].address}
            if 'wlan' in n:
                wf = _gather_wifi(n)
                for k in wf:
                    rv[n][k] = wf[k]
    return rv

