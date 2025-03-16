"""
Tests for log2mqtt.

The tests cover argument parsing, URL parsing, and the main
loop which publishes input from stdin to the MQTT server.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from typing import Sequence
from log2mqtt.__main__ import DEFAULT_PORT, DEFAULT_SCHEME, main_loop, parse_args, parse_url


@pytest.mark.parametrize("args_str,args", [

    # Test with minimum required arguments
    (["-s", "mqtt://192.168.1.1:1883", "-u", "my_user", "-p", "my_pass", "-t", "my_topic"],
     {
        "server": "mqtt://192.168.1.1:1883",
        "username": "my_user",
        "password": "my_pass",
        "topic": "my_topic",
        "verbose": False
     }
    ),

    # Test with optional arguments
    (["-s", "mqtt://myserver.com:1883", "-u", "my_user", "-p", "my_pass", "-t", "my_topic", "-v"],
     {
        "server": "mqtt://myserver.com:1883",
        "username": "my_user",
        "password": "my_pass",
        "topic": "my_topic",
        "verbose": True
     }
    )
])
def test_args(args_str: Sequence[str], args: dict[str, str]):
    """
    Test that the arguments are parsed into the expected format.
    """

    assert vars(parse_args(args_str)) == args



@pytest.mark.parametrize("url,scheme,host,port,transport", [

    # Test minimal URL with defaults
    ("192.168.1.1",
     DEFAULT_SCHEME,
     "192.168.1.1",
     DEFAULT_PORT,
     "tcp"
    ),

    # Test non-standard port
    ("192.168.1.1:1234",
     DEFAULT_SCHEME,
     "192.168.1.1",
     1234,
     "tcp"
    ),

    # Test with name rather than IP
    ("mqtt.myserver.com:9999",
     DEFAULT_SCHEME,
     "mqtt.myserver.com",
     9999,
     "tcp"
    ),

    # Test using encrypted mqtt
    ("mqtts://mqtt.myserver.com:9999",
     "mqtts",
     "mqtt.myserver.com",
     9999,
     "tcp"
    ),

    # Test using web sockets
    ("ws://myserver.com:555",
     "ws",
     "myserver.com",
     555,
     "websockets"
    ),

    # Test using encrypted web sockets
    ("wss://myserver.com:555",
     "wss",
     "myserver.com",
     555,
     "websockets"
    )
])
def test_url_parse(url: str, scheme: str, host: str, port: int, transport: str):
    """
    Test that MQTT server URLs are parsed correctly.
    """

    assert (scheme, host, port, transport) == parse_url(url)



@patch("builtins.input")
def test_main_loop(mocked_input):
    """
    Test the main loop of the program where stdin is published to the 
    MQTT server.

    We expect publish to be called twice with each message containing
    the appropriate entry.
    """

    # Mock input() function used to get stdin
    mocked_input.side_effect = ["Hello there", "Hello again", EOFError]

    # Mock MQTT client with mocked publish function
    mock_client = MagicMock()
    mock_publish_function = MagicMock()
    mock_client.publish = mock_publish_function

    # Run main loop. It will call input until it returns EOFError
    # and then it will exit
    main_loop(mock_client, "my_topic")

    # Assert that the lines would have been published
    mock_publish_function.assert_has_calls([
        call("my_topic", "Hello there"),
        call("my_topic", "Hello again")
    ])
