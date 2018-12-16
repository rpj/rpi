import ctypes as ct

class SPS30(object):
    class Measurement(ct.Structure):
        _fields_ = [("mc_1p0", ct.c_float),
                    ("mc_2p5", ct.c_float),
                    ("mc_4p0", ct.c_float),
                    ("mc_10p0", ct.c_float),
                    ("nc_0p5", ct.c_float),
                    ("nc_1p0", ct.c_float),
                    ("nc_2p5", ct.c_float),
                    ("nc_4p0", ct.c_float),
                    ("nc_10p0", ct.c_float),
                    ("typical_particle_size", ct.c_float)]

    @property
    def driver_version(self):
        return self._dver

    @property
    def serial_number(self):
        return repr(self._devsn.value)

    # an SPS30.Measurement instance
    @property
    def measurement(self):
        return self._get_measurement()

    def __init__(self, shared_object_path="libsps30.so", *args, **kwargs):
        self._lib = ct.cdll.LoadLibrary(shared_object_path)
        if not self._lib:
            raise BaseException("Unable to load shared SPS30 library from '{}'".format(shared_object_path))

        self._lib.sps_get_driver_version.restype = ct.c_char_p
        self._dver = self._lib.sps_get_driver_version()

        if self._lib.sps30_probe() != 0:
            raise BaseException("Probing SPS30 failed")

        self._devsn = ct.create_string_buffer('\000' * 32)
        if self._lib.sps30_get_serial(self._devsn) != 0:
            raise BaseException("Unable to get SPS30 serial number")

        self._measurement_running = False
        self._latest_measurement = None

    def __del__(self):
        self._stop()

    def _stop(self):
        if self._measurement_running:
            self._measurement_running = bool(self._lib.sps30_stop_measurement())

    def _get_measurement(self):
        if not self._measurement_running:
            if self._lib.sps30_start_measurement() != 0:
                raise BaseException("Failed to put SPS30 into measurement mode!")
            self._measurement_running = True
        data_ready = ct.c_byte()
        if self._lib.sps30_read_data_ready(ct.byref(data_ready)) == 0:
            if bool(data_ready.value):
                self._latest_measurement = SPS30.Measurement()
                if self._lib.sps30_read_measurement(ct.byref(self._latest_measurement)) != 0:
                    raise BaseException("read_measurement")
        return self._latest_measurement

if __name__ == "__main__":
    import time
    sps30 = SPS30()
    print "SPS30 S/N {}, driver '{}'".format(sps30.serial_number, sps30.driver_version)
    while 1:
        meas = sps30.measurement
        if meas is not None:
            print ""
            print "PM1.0:\t{}".format(meas.mc_1p0)
            print "PM2.5:\t{}".format(meas.mc_2p5)
            print "PM4.0:\t{}".format(meas.mc_4p0)
            print "PM10.0:\t{}".format(meas.mc_10p0)
            print "NC0.5:\t{}".format(meas.nc_0p5)
            print "NC1.0:\t{}".format(meas.nc_1p0)
            print "NC2.5:\t{}".format(meas.nc_2p5)
            print "NC4.0:\t{}".format(meas.nc_4p0)
            print "NC10.0:\t{}".format(meas.nc_10p0)
            print "TypSz:\t{}".format(meas.typical_particle_size) 
        time.sleep(2)

