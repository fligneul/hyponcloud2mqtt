import pytest
from unittest.mock import MagicMock, patch
from hyponcloud2mqtt.main import Daemon
from hyponcloud2mqtt.config import Config


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.publish_discovery_message')
def test_birth_message_triggers_discovery(
    mock_publish_discovery,
    mock_health_server,
    mock_data_fetcher,
    mock_mqtt_client
):
    """Test that receiving 'online' on HA status topic triggers discovery."""
    # Arrange
    config = Config(
        http_url="http://mock.url",
        system_ids=["12345"],
        http_interval=60,
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_topic="hypon",
        mqtt_availability_topic="hypon/status",
        ha_discovery_enabled=True,
        ha_discovery_prefix="homeassistant"
    )

    mock_mqtt_instance = mock_mqtt_client.return_value
    mock_mqtt_instance.connected = True
    mock_mqtt_instance.connect.return_value = True

    daemon = Daemon(config)

    # We want to trigger the setup logic in Daemon.run()
    # To stop at the fetch loop, we can make fetch_all raise SystemExit or similar
    mock_data_fetcher.return_value.fetch_all.side_effect = SystemExit(0)

    # Act
    with pytest.raises(SystemExit):
        daemon.run()

    # Now verify subscription was called
    mock_mqtt_instance.subscribe.assert_any_call("homeassistant/status")

    # Initial discovery should have been called
    assert mock_publish_discovery.call_count == 1

    # Now simulate the birth message
    callback = mock_mqtt_instance.message_callback
    assert callback is not None

    mock_msg = MagicMock()
    mock_msg.topic = "homeassistant/status"
    mock_msg.payload = b"online"

    # Act
    callback(mock_mqtt_instance, None, mock_msg)

    # Assert
    # Should be 2 now (initial + birth message)
    assert mock_publish_discovery.call_count == 2
    mock_publish_discovery.assert_called_with(mock_mqtt_instance, config, "12345")


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.publish_discovery_message')
def test_other_message_does_not_trigger_discovery(
    mock_publish_discovery,
    mock_health_server,
    mock_data_fetcher,
    mock_mqtt_client
):
    """Test that other messages or 'offline' don't trigger discovery."""
    # Arrange
    config = Config(
        http_url="http://mock.url",
        system_ids=["12345"],
        http_interval=60,
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_topic="hypon",
        mqtt_availability_topic="hypon/status",
        ha_discovery_enabled=True,
        ha_discovery_prefix="homeassistant"
    )

    mock_mqtt_instance = mock_mqtt_client.return_value
    mock_mqtt_instance.connected = True
    mock_mqtt_instance.connect.return_value = True

    daemon = Daemon(config)
    mock_data_fetcher.return_value.fetch_all.side_effect = SystemExit(0)

    with pytest.raises(SystemExit):
        daemon.run()

    # Initial discovery
    assert mock_publish_discovery.call_count == 1

    callback = mock_mqtt_instance.message_callback

    # Act: Send 'offline'
    mock_msg = MagicMock()
    mock_msg.topic = "homeassistant/status"
    mock_msg.payload = b"offline"
    callback(mock_mqtt_instance, None, mock_msg)

    # Assert
    assert mock_publish_discovery.call_count == 1

    # Act: Send random topic
    mock_msg.topic = "homeassistant/other"
    mock_msg.payload = b"online"
    callback(mock_mqtt_instance, None, mock_msg)

    # Assert
    assert mock_publish_discovery.call_count == 1
