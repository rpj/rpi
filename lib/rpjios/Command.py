from __future__ import print_function
import os
import uuid
import json
import redis
import socket
import Util
import Base

COMMAND_NAMESPACE = "rpjios.cmd"
COMMAND_DEFAULT_TTL_SECS = 60
COMMAND_DEBUG_PRINT_LEVEL = 5

CMD_REQUEST_METADATA = "REQ_META"
CMD_ECHO = "ECHO"
CMD_DISCOVER_HELLO = "DISC.HELLO"

_RC_PID = os.getpid()
_RC_HN = socket.gethostname()

def cmd_debug(*args, **kwargs):
    Util.dprint(level=COMMAND_DEBUG_PRINT_LEVEL, *args, **kwargs)

class Remote(Base.Redis):
    def __init__(self, *args, **kwargs):
        super(Remote, self).__init__(*args, **kwargs)
        self._ttl = COMMAND_DEFAULT_TTL_SECS

    def _genRespChan(self, cmd):
        return "{}.CMDRESP:{}:{}:{}:{}".format(COMMAND_NAMESPACE, '_'.join(cmd.split(' ')),
                _RC_HN, _RC_PID, uuid.uuid4())

    def _pubCmdReq(self, cmd, **kwargs):
        cmd_debug("_pubCmdReq({}, {})".format(cmd, kwargs))
        # generate a unique response channel name
        _grc = self._genRespChan(cmd)
        cmd_debug("GRC: {}".format(_grc))
        _cmd = json.dumps({'cmd':cmd, 'resp_chan':_grc})
        _args = json.dumps(kwargs if kwargs else {})

        _rv = None

        # subscribe to our response channel *before* issuing the command request
        self._p.subscribe(_grc)

        # pipeline the request commands for fun and profit
        _pipe = self._r.pipeline()
        # set a key named the same as our response channel containing our args
        _pipe.setex(_grc, self._ttl, _args)
        # publish our command request
        _pipe.publish(COMMAND_NAMESPACE, _cmd)
        if not _pipe.execute()[0]:
            raise Exception("EXEC failed for _pubCmdReq({}, **{})".format(cmd, kwargs))

        for m in self._p.listen():
            if 'subscribe' in m['type']:
                continue
            try:
                _rv = json.loads(m['data'])
                # could leave the key there for as long as we want to allow
                # other entities to respond to our initial cmd request...
                #if not _r.execute_command("DEL", _grc):
                #    raise "Failed to DEL {}".format(_grc)
            except Exception as e:
                print("Failed to serialize response: {}".format(e))
                raise e

            break

        self._p.unsubscribe()
        return _rv

    def requestMetadata(self, **kwargs):
        return self._pubCmdReq(CMD_REQUEST_METADATA, **kwargs) 

    def echo(self, **kwargs):
        return self._pubCmdReq(CMD_ECHO, **kwargs)


class Handler(Base.Redis):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self._handlers = {}
        self._thread = threading.Thread(target=self._hthread)
        self._thread.daemon = True
        self._thread.start()

    def _hthread(self):
        # subscribe to the global command namespace to listen for requests
        self._p.subscribe(COMMAND_NAMESPACE)

        for m in self._p.listen():
            if 'subscribe' in m['type']:
                continue
            try:
                _d = json.loads(m['data'])
                _rs = _d['resp_chan']
                try:
                    # try to get the arguments at the response channel key
                    _kv = json.loads(self._r.get(_rs))

                    # run the registered command handler, passing in arguments
                    # gathered from the above GET
                    _exrv = self._handlers[_d['cmd']](**_kv)

                    # append some metadata to the response
                    _exrv['hostname'] = _RC_HN
                    _exrv['pid'] = _RC_PID
                    _exrv['uuid'] = str(self._uuid)

                    # publish the response to the specified response channel
                    self._r.publish(_rs, json.dumps(_exrv))
                except KeyError:
                    raise Exception("No command handler registered for '{}'!".format(_d['cmd']))
            except Exception as e:
                print("!!!!!\n\tFailure loading data!\n\tERROR: {} {}\n\tDATA:\n\t{}".format(e.__class__.__name__, e, m['data']))
                continue

        self._p.unsubscribe()
   
    def set_handler(self, cmd, handler_func):
        self._handlers[cmd] = handler_func

if __name__ == "__main__":
    import sys
    import time
    import threading
    import collections

    _args = {'host':'localhost', 'password':None}
    if len(sys.argv) < 2:
        print("Usage: {} [server|client] (hostname='{}') (password='{}')".format(sys.argv[0], _args['host'], _args['password']))
        sys.exit(0)

    _keys = ['mode', 'host', 'password']
    _argvc = collections.deque(sys.argv[1:])
    for i in range(len(_argvc)):
        _args[_keys[i]] = _argvc.popleft()

    _mode = _args['mode']
    del _args['mode']

    print("Starting as a {}, using the following connection parameters:\n\t{}".format(_mode, _args))

    if _mode == 'server':
        def my_REQ_META_handler(*args, **kwargs):
            return {"resp": {"msg": "yo whats up homie. here's my metadata", "meta": None}, 
                    "from": "my_REQ_META_handler"}

        def my_ECHO_handler(*args, **kwargs):
            return {"resp": kwargs, "from": "my_ECHO_handler"}

        ch = Handler(**_args)
        ch.set_handler(CMD_REQUEST_METADATA, my_REQ_META_handler)
        ch.set_handler(CMD_ECHO, my_ECHO_handler)
        ch._thread.join()
    elif _mode == 'client':
        rc = Remote(**_args)
        arg = {"an_arg":"an_arg_val"};
        print("requestMetadata({}):".format(arg))
        print("RETURN: {}".format(rc.requestMetadata(**arg)))
        print("echo({}):".format(arg))
        print("RETURN: {}".format(rc.echo(**arg)))

        for i in range(10):
            print("echo({}): {}".format(i, rc.echo(i=i)))
            time.sleep(0.1)
    else:
        raise Exception("Bad mode '{}'!".format(_mode))
