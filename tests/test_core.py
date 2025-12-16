from unittest.mock import MagicMock, patch
from hyponcloud2mqtt.http_client import HttpClient
from hyponcloud2mqtt.mqtt_client import MqttClient


def test_http_client_fetch_success():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 20000, "data": {"key": "value"}}
        mock_get.return_value = mock_response

        client = HttpClient("http://example.com", None)
        data = client.fetch_data()

        assert data == {"code": 20000, "data": {"key": "value"}}


def test_mqtt_client_publish():
    with patch('paho.mqtt.client.Client'):
        client = MqttClient("broker", 1883, "topic", "availability_topic")
        client.connect()

        # Verify LWT set
        client.client.will_set.assert_called_with(
            "availability_topic", "offline", retain=True)

        # Verify online status published on connect
        # We need to simulate the callback
        client._on_connect(client.client, None, None, 0)
        client.client.publish.assert_any_call(
            "availability_topic", "online", retain=True)

        client.publish({"key": "value"})
        client.client.publish.assert_called()


def test_publish_discovery():
    import json
    from hyponcloud2mqtt.config import SensorConfig

    with patch('paho.mqtt.client.Client'):
        client = MqttClient("broker", 1883, "topic", "availability_topic")
        client.connect()

        # Simulate successful connection
        client._on_connect(client.client, None, None, 0)

        sensor = SensorConfig(
            name="Test Sensor",
            unique_id="test_sensor",
            value_template="{{ value_json.test }}",
            device_class="temperature",
            unit_of_measurement="C"
        )

        client.publish_discovery(
            sensor, "device_name", "homeassistant", "state_topic")

        # Verify publish called with correct topic and payload
        assert client.client.publish.called
        # Get the call for discovery (last call might be data publish or online status, so we need to find the right one)
        # But here we only called connect (which calls publish online) and publish_discovery.
        # So we look for the call to the config topic.

        found = False
        for call in client.client.publish.call_args_list:
            args, _ = call
            if args[0] == "homeassistant/sensor/device_name/test_sensor/config":
                found = True
                payload = json.loads(args[1])
                assert payload["name"] == "Test Sensor"
                assert payload["availability_topic"] == "availability_topic"
                assert payload["payload_available"] == "online"
                assert payload["payload_not_available"] == "offline"
                break

        assert found


def test_mqtt_client_dry_run():
    with patch('paho.mqtt.client.Client'):
        # Initialize with dry_run=True
        client = MqttClient("broker", 1883, "topic",
                            "availability_topic", dry_run=True)

        # Test publish
        client.publish({"key": "value"})

        # Verify underlying publish was NOT called
        client.client.publish.assert_not_called()

        # Test publish_discovery
        from hyponcloud2mqtt.config import SensorConfig
        sensor = SensorConfig(
            name="Test Sensor",
            unique_id="test_sensor",
            value_template="{{ value_json.test }}"
        )
        client.publish_discovery(sensor, "device", "prefix", "topic")

        # Verify underlying publish was still NOT called
        client.client.publish.assert_not_called()


def test_mqtt_client_tls():
    with patch('paho.mqtt.client.Client'):
        # Enable TLS
        client = MqttClient(
            "broker",
            1883,
            "topic",
            "availability_topic",
            tls_enabled=True,
            tls_insecure=True,
            ca_path="/tmp/ca.crt")

        # Verify tls_set called
        client.client.tls_set.assert_called_with(ca_certs="/tmp/ca.crt")
        # Verify tls_insecure_set called
        client.client.tls_insecure_set.assert_called_with(True)


def test_mqtt_client_disconnect_publishes_offline():
    """Test that disconnect publishes offline status before disconnecting."""
    with patch('paho.mqtt.client.Client'):
        client = MqttClient("broker", 1883, "topic", "availability_topic")

        # Simulate successful connection
        client.connect()
        client._on_connect(client.client, None, None, 0)

        # Mock the publish return value
        mock_info = MagicMock()
        client.client.publish.return_value = mock_info

        # Call disconnect
        client.disconnect()

        # Verify offline status was published
        client.client.publish.assert_any_call(
            "availability_topic", "offline", retain=True)

        # Verify wait_for_publish was called with timeout
        mock_info.wait_for_publish.assert_called_once_with(timeout=2.0)

        # Verify disconnect was called
        client.client.disconnect.assert_called_once()


def test_mqtt_client_disconnect_dry_run():
    """Test that disconnect in dry run mode doesn't publish offline."""
    with patch('paho.mqtt.client.Client'):
        client = MqttClient("broker", 1883, "topic",
                            "availability_topic", dry_run=True)

        # Call disconnect
        client.disconnect()

        # Verify offline status was NOT published (dry run mode)
        # Only will_set should have been called during init
        assert client.client.publish.call_count == 0

        # Verify disconnect was still called
        client.client.disconnect.assert_called_once()
