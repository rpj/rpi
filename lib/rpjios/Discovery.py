import Base
import Util
import time
import json
import urllib2
import socket
from datetime import datetime

# TODO: define this shit once and for all somewhere...
NAMESPACE = 'rpjios'

class Discovery(Base.Redis):
    def __init__(self, *args, **kwargs):
        super(Discovery, self).__init__(*args, **kwargs)

    def checkin(self):
        cd = {'ext_ip':None, 'up':Util.uptime(),'lt':str(datetime.now()),'host':socket.gethostname(),'ifaces':Util.network_ifaces()}

        try:
            cd['ext_ip'] = json.loads(urllib2.urlopen("https://api.ipify.org?format=json").read())['ip']
        except:
            pass

        # returns the number of *added* keys, so may be zero even in success. basically, a terrible return value here.
        return reduce(lambda x, a: x + a, map(lambda k: self._r.hset("{}.checkin.{}".format(NAMESPACE, cd['host']), k, json.dumps(cd[k])), cd))

if __name__ == "__main__":
    d = Discovery(**Util.cur_redis_dict())
    print "{}: added {} keys".format(d, d.checkin())
