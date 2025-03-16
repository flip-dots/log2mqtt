# log2mqtt

Simple Python program to publish standard input to an MQTT server on a desired topic.

## Installation

The program can be installed using PIP.

```bash
pip install log2mqtt
```

## Usage

Expected usage of the program is piping the standard output of a program you want to
monitor the logs of into into the program. This looks something like:

```bash
my_program | python3 -m log2mqtt -s wss://mqtt.myserver.com:443 -u my_user -p my_pass -t /my_mqtt_topic
```

## What Does It Do?

It publishes the standard output of the piped program to an MQTT server. Each break in the standard output is published as a new message and this program exits cleanly when the logged process terminates.

## But Why?

I made a custom home assistant card which reads the sensor history of an MQTT sensor and renders it as a terminal, this allows me to monitor the logs of my scripts right in my home assistant instance without having to mess around with more complicated logging tools.
