# RPJiOS

A [pub/sub](https://en.wikipedia.org/wiki/Publish–subscribe_pattern)-based implementation of a 
Raspberry Pi system platform built on [redis](https://redis.io) and centered around sensors.

The general philosophy is that a "sensor" is any entity (physical or not) that operates primarily
in an output-only mode (configuration doesn't necessarily count as an "input" so is allowable).

These outputs are treated ephemerally, in a "fire and forget" manner, creating a data stream.
The intent is for interested entities to subscribe to the data stream and transform, interpret 
and/or persist it according to their requirements.

## Caveat emptor

This is still very much an active work-in-progress, however as it is functional, useful and "deployed" 
(I use it in to run my "garden monitoring bots"), I figured it was worth making public in the event it
might help others in their projects.

## Requirements

* a Raspberry Pi running a recent Raspbian build
	* (not exactly: it should run on any linux OS, and definitely does on any "Debian-like" OS but needs a bit of tweaks to do so. TODO: fix that; it's already running on charlie anyway)
* some sensors, configured appropriately (see below (TODO))
	* depending on your chosen sensors: I2C enabled, SPI enabled (TODO: link to instructions)
* `virtualenv` (python2.7)
* `redis` (running locally, at very least)
* `python-smbus`

## Setup

* Clone the repo
* `cd` into repo dir
* `./setup.sh` (you might need to enter your `sudo` password to install requirements)
* `source env/bin/activate` and go

## Tools

* [sensors-src](bin/sensors-src): source daemon that manages all specified sensors and publishes their data as configured
* [downsample](bin/downsample): a downsampler/transformer(TODO). example uses:
	* an at-frequency forwarder (set `-r 1`)
	* a loopback downsampler (set `-o` to the same as `-i`)
	* a many-to-one reducer (set `-t` to `key`, lots of potential "TODO" here)
* [sqlite-sink](bin/sqlite-sink): an [SQLite](https://www.sqlite.org) sink for data streams. examples:
	* sink to an SQLite database on a different host a downsampled data stream:
		1. on the source device:
			* `downsample -i redis://localhost -o redis://sql-db-host -r ... -p ...`
		2. on the sink host "`sql-db-host`":
			* `sqlite-sink path-to-db.sqlite3`
				* (lots of "TODOs" here, obviously) 
* [oled-display](bin/oled-display): an [OLED display](https://www.adafruit.com/product/661) driver for consuming & display some sensor data, among other things

## Library

### Sensors & Devices

The following are currently supported (with the required drivers / interfaces setup of course):

* [BME680](https://cdn-shop.adafruit.com/product-files/3660/BME680.pdf) temperature / humidity / barometeric pressure / volatic organic compound sensor. My setup uses [AdaFruit's awesome breakout board](https://www.adafruit.com/product/3660) for ease-of-integration. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/BME680.py)
* [DHTXX](https://www.mouser.com/ds/2/737/dht-932870.pdf)(DHT11/DHT22) temperature / humidity sensors. I use [DFRobot's](https://www.dfrobot.com/product-1102.html) [breakouts](https://www.dfrobot.com/product-174.html) but you can find similar breakout's from many (re)sellers online. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/DHTXX.py)
* [DS18S20](https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf) high-precision 1-wire temperature sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/DS18S20.py)
* [LM335](http://www.ti.com/lit/ds/symlink/lm335.pdf) precision analog temperature sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/LM335.py)
* Capacative soil moisture sensors such as the DFRobot [SEN0114](https://www.dfrobot.com/product-599.html) or any [simple-to-build capactive analog moisture sensor](http://gardenbot.org/howTo/soilMoisture/). [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/Soil.py)
* [TEPT5700](https://www.vishay.com/docs/81321/tept5700.pdf) ambient light sensor.

Variants of these sensors could likely be made to work with this system via simple modifications if any are required at all.

Additionally, a simple Python driver for the [74HC595](http://www.ti.com/lit/ds/symlink/sn74hc595.pdf) 8-bit shift register is included [here](https://github.com/rpj/rpi/blob/master/lib/rpjios/devices/74HC595.py).

## Related

* [RPJiOS-Web](https://github.com/rpj/rpjios-web): A [Flask](http://flask.pocoo.org/) web frontend currently deployed as [rpjios.com](http://rpjios.com) on [Heroku](http://heroku.com)
	* Demonstrates the use of the `-t key` passthru mode of `downsample`, e.g.:
		* `downsample -t 'key' -i 'redis://localhost' -o 'redis://REDACTED@ec2-REDACTED.compute-1.amazonaws.com:REDACTED' -p 'rpjios.sensors.*'`
* [The old now-archived repository](https://github.com/rpj/rpi.archive) from whence this all came
	* might still contain some useful stuff: D3-based "live" analog data plotting code in `rpjctrl`, and I'm still using `ledCount.py` on some of my units because I'm too lazy to re-write it properly

## License

Copyright 2018 Ryan P. Joseph <ryan.joseph@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
