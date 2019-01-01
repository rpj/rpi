import RedisBase
import Util
import time
import json
import urllib2
import socket
from datetime import datetime

# TODO: define this shit once and for all somewhere...
NAMESPACE = 'rpjios'

DEFAULT_TTL = 5 # minutes

class Discovery(RedisBase.Redis):
    def __init__(self, *args, **kwargs):
        super(Discovery, self).__init__(*args, **kwargs)

    def _checkin_set_host(self, cd):
        hname = "{}.checkin.{}".format(NAMESPACE, cd["host"])
        added = reduce(lambda x, a: x + a, map(lambda k: self._r.hset(hname, k, json.dumps(cd[k])), cd))
        self._r.expire(hname, DEFAULT_TTL * 60)

    def checkin(self):
        cd = {'ext_ip':None, 'up':Util.uptime(),'lt':str(datetime.now()),'host':Util.hostname(),'ifaces':Util.network_ifaces()}

        try:
            cd['ext_ip'] = json.loads(urllib2.urlopen("https://api.ipify.org?format=json").read())['ip']
        except:
            pass

        return self._checkin_set_host(cd)

if __name__ == "__main__":
    Discovery().checkin()
