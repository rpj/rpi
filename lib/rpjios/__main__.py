import Sensors
import time

if __name__ == '__main__':
    print "RPIOS.Sensors unit test"
    s = Sensors.Sensors()
    print "LIST: {}".format(s.list())
    b = s.create(s.list()[0])
    print "Starting {}".format(b)
    def listen_func(m):
        print "listen got message '{}'".format(m)

    b.subscribe_to(listen_func)
    b.start()
    print "{} metadata:\n{}\n".format(b, b.metadata())

    time.sleep(10)
    print "Done"
    b.stop()
    print "Really done"
