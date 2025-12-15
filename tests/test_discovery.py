import pytest
from unittest.mock import patch, MagicMock
from hyponcloud2mqtt.config import Config, SensorConfig
from hyponcloud2mqtt.main import Daemon


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.Config.load')
def test_discovery_disabled(
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
        ha_discovery_enabled=False,
        sensors=[
            SensorConfig(
                name="test",
                unique_id="test",
                value_template="test")]
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
    mock_mqtt_instance.publish_discovery.assert_not_called()


@patch('hyponcloud2mqtt.main.MqttClient')
@patch('hyponcloud2mqtt.main.DataFetcher')
@patch('hyponcloud2mqtt.main.HealthServer')
@patch('hyponcloud2mqtt.main.Config.load')
def test_discovery_enabled(
        mock_config_load, mock_health_server, mock_data_fetcher, mock_mqtt_client):
    """Test that discovery messages are published when discovery is enabled."""
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
        sensors=[
            SensorConfig(
                name="test",
                unique_id="test",
                value_template="test")],
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
    mock_mqtt_instance.publish_discovery.assert_called_once()
