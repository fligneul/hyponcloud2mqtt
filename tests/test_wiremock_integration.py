from __future__ import annotations
import json
import logging
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
    Also verifies that Home Assistant discovery messages are published.
    """
    # Enable HA discovery for this test
    test_config.ha_discovery_enabled = True
    test_config.ha_discovery_prefix = "homeassistant"

    # Use a real MQTT client to subscribe and receive the message
    received_messages = []
    # Events to signal we got what we wanted
    data_received_event = threading.Event()
    discovery_received_event = threading.Event()
    online_received_event = threading.Event()
    offline_received_event = threading.Event()

    data_topic = f"{test_config.mqtt_topic}/{test_config.system_ids[0]}"
    discovery_topic_prefix = f"{test_config.ha_discovery_prefix}/sensor/hypon_{test_config.system_ids[0]}"

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        logger.info(f"Received message on {msg.topic}")

        if msg.topic == data_topic:
            received_messages.append({"type": "data", "payload": json.loads(payload)})
            data_received_event.set()
        elif msg.topic.startswith(discovery_topic_prefix):
            received_messages.append({"type": "discovery", "topic": msg.topic, "payload": json.loads(payload)})
            # We expect multiple, but receiving one is enough to prove the feature works for this integration test
            discovery_received_event.set()
        elif msg.topic == test_config.mqtt_availability_topic:
            received_messages.append({"type": "availability", "payload": payload})
            if payload == "online":
                online_received_event.set()
            elif payload == "offline":
                offline_received_event.set()

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_message

    # Configure logging for the test
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        mqtt_client.connect(test_config.mqtt_broker, test_config.mqtt_port, 60)
    except (ConnectionRefusedError, OSError) as e:
        pytest.skip(f"MQTT broker not running on {test_config.mqtt_broker}:{test_config.mqtt_port}: {e}")

    # Subscribe to data topic, discovery topics, and availability topic
    mqtt_client.subscribe([
        (data_topic, 0),
        (f"{test_config.ha_discovery_prefix}/#", 0),
        (test_config.mqtt_availability_topic, 0)
    ])

    # Start the MQTT client loop in a separate thread
    mqtt_client.loop_start()

    # We need to patch the signal handler to prevent the test from exiting
    # prematurely
    with patch("signal.signal"):
        # We also need to disable the health server to avoid port conflicts
        # with wiremock
        test_config.health_server_enabled = False
        daemon = Daemon(test_config)

        daemon_thread = threading.Thread(target=daemon.run, daemon=True)
        daemon_thread.start()

        # Wait for the messages to be received, with a timeout
        online_ok = online_received_event.wait(timeout=10)
        data_ok = data_received_event.wait(timeout=10)
        discovery_ok = discovery_received_event.wait(timeout=10)

        daemon.running = False
        daemon_thread.join(timeout=5)

        # After daemon stops, it should publish offline status
        offline_ok = offline_received_event.wait(timeout=5)

    # Stop the MQTT client loop
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    assert online_ok, "Test timed out waiting for online MQTT message"
    assert data_ok, "Test timed out waiting for data MQTT message"
    assert discovery_ok, "Test timed out waiting for discovery MQTT message"
    assert offline_ok, "Test timed out waiting for offline MQTT message"

    # Verify Data
    data_message = next((m for m in received_messages if m["type"] == "data"), None)
    assert data_message is not None

    # Dynamically generate expected data from wiremock resources
    with open("wiremock/mappings/monitor.json") as f:
        monitor_data = json.load(f)["response"]["jsonBody"]
    with open("wiremock/mappings/production.json") as f:
        production_data = json.load(f)["response"]["jsonBody"]
    with open("wiremock/mappings/status.json") as f:
        status_data = json.load(f)["response"]["jsonBody"]

    expected_data = merge_api_data(monitor_data, production_data, status_data)
    assert data_message["payload"] == expected_data

    # Verify Discovery
    discovery_messages = [m for m in received_messages if m["type"] == "discovery"]
    assert len(discovery_messages) > 0, "No discovery messages received"

    # Check one random discovery message for correctness
    sample_discovery = discovery_messages[0]
    payload = sample_discovery["payload"]
    assert "name" in payload
    assert "state_topic" in payload
    assert payload["state_topic"] == data_topic
    assert "unique_id" in payload
    assert "device" in payload
    assert payload["device"]["manufacturer"] == "Hypon"
