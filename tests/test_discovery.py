import pytest
from unittest.mock import patch, MagicMock
from hyponcloud2mqtt.config import Config
from hyponcloud2mqtt.main import Daemon
from hyponcloud2mqtt.discovery import publish_discovery_message


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.Config.load')
@patch('hyponcloud2mqtt.main.publish_discovery_message')
def test_discovery_disabled(
        mock_publish_discovery,
        mock_config_load, mock_health_server, mock_data_fetcher, mock_mqtt_client):
    """Test that no discovery messages are published when discovery is disabled."""
    # Arrange
    config = Config(
        http_url="http://mock.url",
        system_ids=["12345"],
        http_interval=60,
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_topic="hypon",
        mqtt_availability_topic="hypon/status",
        ha_discovery_enabled=False
    )
    mock_config_load.return_value = config
    mock_mqtt_instance = mock_mqtt_client.return_value
    mock_mqtt_instance.connected = True

    daemon = Daemon(config)
    daemon.running = False

    # Act
    try:
        daemon.run()
    except SystemExit as e:
        assert e.code == 0

    # Assert
    mock_publish_discovery.assert_not_called()


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.Config.load')
@patch('hyponcloud2mqtt.main.publish_discovery_message')
def test_discovery_enabled(
        mock_publish_discovery,
        mock_config_load, mock_health_server, mock_data_fetcher, mock_mqtt_client):
    """Test that discovery messages are published when discovery is enabled."""
    # Arrange
    config = Config(
        http_url="http://mock.url",
        system_ids=["12345", "67890"],
        http_interval=60,
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_topic="hypon",
        mqtt_availability_topic="hypon/status",
        ha_discovery_enabled=True,
        dry_run=False
    )
    mock_config_load.return_value = config
    mock_mqtt_instance = mock_mqtt_client.return_value
    mock_mqtt_instance.connected = True
    mock_data_fetcher.return_value.fetch_all.side_effect = SystemExit(0)

    daemon = Daemon(config)

    # Act
    with pytest.raises(SystemExit) as e:
        daemon.run()
    assert e.value.code == 0

    # Assert
    assert mock_publish_discovery.call_count == 2
    mock_publish_discovery.assert_any_call(mock_mqtt_instance, config, "12345")
    mock_publish_discovery.assert_any_call(mock_mqtt_instance, config, "67890")


def test_publish_discovery_message_contains_precision():
    # Arrange
    client = MagicMock()
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
    system_id = "12345"

    # Act
    publish_discovery_message(client, config, system_id)

    # Assert
    # Check at least one numeric sensor (e.g., today_generation)
    found = False
    for call in client.publish.call_args_list:
        payload = call.args[0] if call.args else call.kwargs.get('payload')
        topic = call.kwargs.get('topic') or (call.args[1] if len(call.args) > 1 else None)

        if "today_generation" in (topic or ""):
            assert payload["suggested_display_precision"] == 2
            found = True
            break

    assert found, "Discovery message for today_generation not found"


def test_publish_discovery_message_no_precision_for_diagnostic():
    # Arrange
    client = MagicMock()
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
    system_id = "12345"

    # Act
    publish_discovery_message(client, config, system_id)

    # Assert
    # Check a diagnostic sensor (e.g., gateway_online)
    found = False
    for call in client.publish.call_args_list:
        payload = call.args[0]
        topic = call.kwargs.get('topic')

        if "gateway_online" in topic:
            assert "suggested_display_precision" not in payload
            found = True
            break

    assert found, "Discovery message for gateway_online not found"
