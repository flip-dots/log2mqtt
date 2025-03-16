"""
log2mqtt

Simple Python script to pipe standard input to an MQTT server.
"""

import argparse
import logging
import paho.mqtt.client as mqtt
import re
import sys
from typing import Sequence
from urllib.parse import urlparse


DEFAULT_SCHEME = "mqtt"
DEFAULT_PORT = 1883

ALLOWED_SCHEMES = ["mqtt", "mqtts", "ws", "wss"]


logger = logging.getLogger(__name__)


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    """
    Parse arguments provided to program.

    :param args: Arguments provided to program.
    :returns: Parsed arguments.
    """

    parser = argparse.ArgumentParser(
        prog="log2mqtt",
        description="Pipe standard input to an MQTT server",
        epilog="Use this program like 'my_program | python3 -m log2mqtt -s wss://mqtt.myserver.com:443 -u my_user -p my_pass -t /my_mqtt_topic'"
    )

    parser.add_argument("-s", "--server", required=True)
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-t", "--topic", required=True)
    parser.add_argument("-v", "--verbose", action="store_true")

    return parser.parse_args(args)


def parse_url(url_str: str) -> tuple[str, str, int, str]:
    """
    Parse URL into parameters required by paho-mqtt.

    :param url: URL string to parse.
    :returns: Scheme (e.g wss://mqtt.myserver.com:443 -> wss).
    :returns: Host (e.g wss://mqtt.myserver.com:443 -> mqtt.myserver.com).
    :returns: Port (e.g wss://mqtt.myserver.com:443 -> 443).
    :returns: Transport (e.g wss://mqtt.myserver.com:443 -> websockets).
    """

    # If URL scheme not specified then use default
    if not any(url_str.startswith(f"{scheme}://") for scheme in ALLOWED_SCHEMES):
        url_str = f"{DEFAULT_SCHEME}://{url_str}"

    url = urlparse(url_str)

    port = url.port if url.port else DEFAULT_PORT

    # If the URL scheme equals ws(s) then we are using websockets, else tcp
    transport = "websockets" if bool(re.match(r"wss?", url.scheme)) else "tcp"

    return url.scheme, url.hostname, port, transport


def setup_mqtt(scheme: str, host: str, port: int, transport: str, username: str, password: str) -> mqtt.Client:
    """
    Setup MQTT client using program arguments, setups up callbacks, and connects to the server.

    :param scheme: Scheme to use to connect to MQTT server (i.e mqtt, mqtts, ws, wss).
    :param host: Host of MQTT server to connect to (e.g mqtt.myserver.com).
    :param port: Port of MQTT server to connect to (e.g 443, 1883, 8883, etc).
    :param transport: Use Websockets or TCP (i.e 'websockets or 'tcp').
    :param username: The username to connect to the MQTT server as.
    :param password: The password of the user on the MQTT server.
    :returns: Connected MQTT client.
    """

    # Init client and setup auth
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True, transport=transport)
    client.username_pw_set(username, password)

    # If using encrypted scheme then setup tls
    if scheme in ["mqtts", "wss"]:
        client.tls_set()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            logger.warning("Failed to connect to MQTT server. Will automatically reconnect")
        else:
            logger.info("Connected to MQTT server!")

    def on_disconnect(client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            logger.warning("Unexpected MQTT disconnection. Will automatically reconnect")
        else:
            logger.info("Disconnected from MQTT server!")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Connect to server
    logger.info(f"Connecting to MQTT server '{host}' at port '{port}' using transport '{transport}'...")
    client.connect(host, port)

    # Start non-blocking loop to keep client alive
    client.loop_start()

    # Block until client is connected
    while not client.is_connected():
        pass

    return client


def main_loop(client: mqtt.Client, topic: str) -> None:
    """
    Read stdin and publish lines to MQTT server.
    Runs in an infinite loop until the program being logged terminates.

    :param client: MQTT client to use to publish messages.
    :param topic: MQTT topic to publish messages to.
    """

    while True:

        try:
            # Get input and publish to MQTT server
            line = input()
            logger.debug(f"Input from program: '{line}'")
            client.publish(topic, line)

        # Exit loop on monitored program terminating
        except EOFError as e:
            logger.error(f"Program being logged was terminated! E: '{e}'")
            break


def main(args: Sequence[str]):
    """
    Main program.

    Publishes output of stdin to the MQTT server.
    """

    # Parse arguments provided to program
    args = parse_args(args)

    # Configure logging level
    logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))

    # Parse MQTT server URL
    scheme, host, port, transport = parse_url(args.server)

    # Connect to MQTT server
    client = setup_mqtt(scheme, host, port, transport, args.username, args.password)

    # Execute blocking main loop
    main_loop(client, args.topic)

    # Disconnect and stop MQTT client
    client.disconnect()
    client.loop_stop()
    logger.info("Program exiting!")


if __name__ == "__main__":
    main(sys.argv[1:])
