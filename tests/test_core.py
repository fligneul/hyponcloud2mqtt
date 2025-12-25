from unittest.mock import MagicMock, patch
from hyponcloud2mqtt.http_client import HttpClient
from hyponcloud2mqtt.mqtt_client import MqttClient


def test_http_client_fetch_success():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": 20000, "data": {"key": "value"}}
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    client = HttpClient("http://example.com", mock_session)
    data = client.fetch_data()

    assert data == {"code": 20000, "data": {"key": "value"}}
    mock_session.get.assert_called_once()


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


def test_mqtt_client_dry_run():
    with patch('paho.mqtt.client.Client'):
        # Initialize with dry_run=True
        client = MqttClient("broker", 1883, "topic",
                            "availability_topic", dry_run=True)

        # Test publish
        client.publish({"key": "value"})

        # Verify underlying publish was NOT called
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
