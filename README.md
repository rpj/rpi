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

(TODO)

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
