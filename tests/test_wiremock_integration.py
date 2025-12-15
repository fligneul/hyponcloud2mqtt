from __future__ import annotations
import json
import os
import threading
from unittest.mock import patch

import paho.mqtt.client as mqtt
import pytest

from hyponcloud2mqtt.config import Config
from hyponcloud2mqtt.data_merger import merge_api_data
from hyponcloud2mqtt.main import Daemon

@pytest.fixture
def test_config():
    """
    Fixture to create a test configuration from environment variables.
    Skips the test if the required environment variables are not set.
    """
    if not os.getenv("HTTP_URL"):
        pytest.skip("Skipping integration test: HTTP_URL not set")

    return Config.load()


def test_daemon_fetches_and_publishes_data(test_config):
    """
    Integration test to verify the daemon fetches data from WireMock and
    publishes to a test MQTT broker.
    """
    # Use a real MQTT client to subscribe and receive the message
    received_message = None
    message_received_event = threading.Event()
    topic = f"{test_config.mqtt_topic}/{test_config.system_ids[0]}"

    def on_message(client, userdata, msg):
        nonlocal received_message
        received_message = json.loads(msg.payload.decode())
        message_received_event.set()
        client.disconnect()

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(test_config.mqtt_broker, test_config.mqtt_port, 60)
    except (ConnectionRefusedError, OSError):
        pytest.skip("MQTT broker not running on localhost")

    mqtt_client.subscribe(topic)

    # Start the MQTT client loop in a separate thread
    mqtt_client.loop_start()

    # We need to patch the signal handler to prevent the test from exiting prematurely
    with patch("signal.signal") as mock_signal:
        # We also need to disable the health server to avoid port conflicts with wiremock
        test_config.health_server_enabled = False
        daemon = Daemon(test_config)

        daemon_thread = threading.Thread(target=daemon.run, daemon=True)
        daemon_thread.start()

        # Wait for the message to be received, with a timeout
        message_received = message_received_event.wait(timeout=10)

        daemon.running = False
        daemon_thread.join(timeout=5)

    # Stop the MQTT client loop
    mqtt_client.loop_stop()

    assert message_received, "Test timed out waiting for MQTT message"
    assert received_message is not None

    # Dynamically generate expected data from wiremock resources
    with open("wiremock/mappings/monitor.json") as f:
        monitor_data = json.load(f)["response"]["jsonBody"]
    with open("wiremock/mappings/production.json") as f:
        production_data = json.load(f)["response"]["jsonBody"]
    with open("wiremock/mappings/status.json") as f:
        status_data = json.load(f)["response"]["jsonBody"]

    expected_data = merge_api_data(monitor_data, production_data, status_data)

    assert received_message == expected_data
