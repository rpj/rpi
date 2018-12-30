# RPJiOS

[![Raspberry Pi Zero W](https://www.vectorlogo.zone/logos/raspberrypi/raspberrypi-ar21.svg)](https://www.raspberrypi.org/)
[![Python](https://www.vectorlogo.zone/logos/python/python-ar21.svg)](https://www.python.org/)
[![Redis](https://www.vectorlogo.zone/logos/redis/redis-ar21.svg)](https://redis.io/)
[![Debian](https://www.vectorlogo.zone/logos/debian/debian-ar21.svg)](https://www.raspbian.org/)

A [pub/sub](https://en.wikipedia.org/wiki/Publish–subscribe_pattern)-based implementation of a 
Raspberry Pi data pipeline built on [redis](https://redis.io) and centered around sensors.

The general philosophy is that a "sensor" is any entity (physical or not) that operates primarily
in an output-only mode (configuration doesn't necessarily count as an "input" so is allowable).

These outputs are treated ephemerally, in a "fire and forget" manner, creating a data stream.
The intent is for interested entities to subscribe to the data stream and transform, interpret 
and/or persist it according to their requirements.

## Caveat emptor

This is still very much an active work-in-progress! However, as it is functional and actively deployed I figured it was worth making public in the event it might help others in their projects.

Those current deployments consist of my [atmospheric particulate matter sensor](https://www.hackster.io/rpj/atmospheric-particulate-matter-environmental-sensing-fb31a1) and my garden monitoring bots, with the entire system handling (on average) about a half-million units of sensor data per day.

## Requirements

* Hardware:
	* a Raspberry Pi running a recent Raspbian build (for sensor nodes)
	* any Debian-like system running apt (for managment/non-sensor nodes)
* some [sensors](#sensors), configured appropriately (most easily done with `raspi-config`):
	* depending on your chosen sensors: I2C enabled, SPI enabled, 1-wire enabled
	* other sensors (LM335, Soil, TEPT5700) require an [external ADC](#devices) which itself will require SPI

## Setup

* Clone the repo
* `cd` into repo dir
* `./setup.sh` (you might need to enter your `sudo` password to install requirements)
* `source env/bin/activate` and go!

## Tools

* [sensors-src](bin/sensors-src): source daemon that manages all specified sensors and publishes their data as configured
* [downsample](bin/downsample): a very flexible data stream downsampler/forwarder/transformer. example uses:
	* an at-frequency forwarder (set `-r 1`)
	* a loopback downsampler (set `-o` to the same as `-i`)
	* a many-to-one reducer (set `-t` to `key`)
	* a one-to-many exploder (set `-m` to `flatten:[options]`)
	* a bounded ephemeral cache (set `-t` to `list:[options]`, where the `limit=X` option sets the bound)
	* ...
	* profit!
* [sqlite-sink](bin/sqlite-sink): an [SQLite](https://www.sqlite.org) sink for data streams. examples:
	* sink to an SQLite database on a different host a downsampled data stream:
		1. on the source device:
			* `downsample -i redis://localhost -o redis://sql-db-host -r ... -p ...`
		2. on the sink host "`sql-db-host`":
			* `sqlite-sink path-to-db.sqlite3`
				* (lots of "TODOs" here, obviously) 
* [oled-display](bin/oled-display): an [OLED display](https://www.adafruit.com/product/661) driver for consuming & display some sensor data, among other things
* [thingspeak](bin/thingspeak): a simple example of a [ThingSpeak](http://thingspeak.com) data forwarder for the SPS30 particulate matter sensor data. [Example resulting data set](https://thingspeak.com/channels/655525).

## Library

### Sensors

The following are currently supported (with the required drivers / interfaces setup of course):

* [SPS30](https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/) I2C particulate matter air quality sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/SPS30.py)
* [BME680](https://cdn-shop.adafruit.com/product-files/3660/BME680.pdf) temperature / humidity / barometeric pressure / volatile organic compound I2C sensor. My setup uses [AdaFruit's awesome breakout board](https://www.adafruit.com/product/3660) for ease-of-integration. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/BME680.py)
* [BME280](https://www.bosch-sensortec.com/bst/products/all_products/bme280) temperature / humidity / barometeric pressure I2C sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/BME280.py)
* [DHTXX](https://www.mouser.com/ds/2/737/dht-932870.pdf)(DHT11/DHT22) temperature / humidity sensors. I use [DFRobot's](https://www.dfrobot.com/product-1102.html) [breakouts](https://www.dfrobot.com/product-174.html) but you can find similar breakout's from many (re)sellers online. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/DHTXX.py)
* [DS18S20](https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf) high-precision 1-wire temperature sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/DS18S20.py)
* [LM335](http://www.ti.com/lit/ds/symlink/lm335.pdf) precision analog temperature sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/LM335.py)
* Capacative soil moisture sensors such as the DFRobot [SEN0114](https://www.dfrobot.com/product-599.html) or any [simple-to-build capactive analog moisture sensor](http://gardenbot.org/howTo/soilMoisture/). [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/Soil.py)
* [TEPT5700](https://www.vishay.com/docs/81321/tept5700.pdf) ambient light sensor. [Source.](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/TEPT5700.py)
* "Virtual" sensors such as [SysInfo](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/SysInfo.py) and [NetInfo](https://github.com/rpj/rpi/blob/master/lib/rpjios/sensors/NetInfo.py) that do not require any additional hardware.

Variants of these sensors could likely be made to work with this system via simple modifications if any are required at all.

### Devices

* A simple Python wrapper driver for the SPS30 sensor is included [here](https://github.com/rpj/rpi/blob/master/lib/rpjios/devices/SPS30.py), wrapping the included [embedded-sps](https://github.com/rpj/embedded-sps/tree/1aabaead20059262d66e113d511157c6fda4133a) I2C driver from Sensiron implemented in C (forked to include a shared object build step for Python consumption). 
* A simple Python driver for the [74HC595](http://www.ti.com/lit/ds/symlink/sn74hc595.pdf) 8-bit shift register is included [here](https://github.com/rpj/rpi/blob/master/lib/rpjios/devices/74HC595.py).
* The venerable [MCP3008](http://ww1.microchip.com/downloads/en/devicedoc/21295c.pdf) 10-bit 8-channel analog-to-digital converter is directly supported by the [base analog sensor implementation](https://github.com/rpj/rpi/blob/master/lib/rpjios/AnalogBase.py). Other ADCs would be quite simple to adapt (even more so if I implemented a HAL... #TODO).
	* channel (zero-indexed) is specified in [`config.json`](https://github.com/rpj/rpi/blob/master/config.json#L62)

## Related

* [The old now-archived repository](https://github.com/rpj/rpi.archive) from whence this all came
	* might still contain some useful stuff: D3-based "live" analog data plotting code in `rpjctrl`, and I'm still using `ledCount.py` on some of my units because I'm too lazy to re-write it properly
