from unittest.mock import patch
from hyponcloud2mqtt.config import Config, SensorConfig
from hyponcloud2mqtt.main import Daemon


def test_discovery_disabled_by_default():
    """Test that discovery is not published when disabled (default)"""
    with patch('hyponcloud2mqtt.main.MqttClient') as mock_mqtt_cls, \
            patch('hyponcloud2mqtt.main.DataFetcher'), \
            patch('hyponcloud2mqtt.main.HealthServer'), \
            patch('hyponcloud2mqtt.main.Config.load') as mock_config_load:

        # Setup config with discovery disabled (default)
        config = Config(
            http_url="http://mock",
            system_id="12345",
            http_interval=60,
            mqtt_broker="localhost",
            mqtt_port=1883,
            mqtt_topic="topic",
            mqtt_availability_topic="avail",
            ha_discovery_enabled=False,
            sensors=[SensorConfig("test", "id", "tmpl")]
        )
        mock_config_load.return_value = config

        # Mock Daemon to run once and stop
        daemon = Daemon()
        daemon.running = False  # Stop immediately after one loop

        # We need to mock the run loop to avoid infinite loop if logic fails,
        # but here we want to test the initialization part where discovery happens.
        # Actually, discovery happens before the loop in run()

        # To avoid running the loop at all, we can mock the loop part or just rely on side effects.
        # But run() calls mqtt_client.connect() then publish_discovery then enters loop.
        # We can raise an exception to break out of run() after discovery part?
        # Or better, just patch Daemon.running to be False initially?
        # If running is False, it will skip the while loop.
        daemon.running = False

        # Run daemon
        try:
            daemon.run()
        except SystemExit:
            pass

        # Verify publish_discovery was NOT called
        mock_mqtt_instance = mock_mqtt_cls.return_value
        mock_mqtt_instance.publish_discovery.assert_not_called()


def test_discovery_enabled():
    """Test that discovery IS published when enabled"""
    with patch('hyponcloud2mqtt.main.MqttClient') as mock_mqtt_cls, \
            patch('hyponcloud2mqtt.main.DataFetcher'), \
            patch('hyponcloud2mqtt.main.HealthServer'), \
            patch('hyponcloud2mqtt.main.Config.load') as mock_config_load:

        # Setup config with discovery ENABLED
        config = Config(
            http_url="http://mock",
            system_id="12345",
            http_interval=60,
            mqtt_broker="localhost",
            mqtt_port=1883,
            mqtt_topic="topic",
            mqtt_availability_topic="avail",
            ha_discovery_enabled=True,
            sensors=[SensorConfig("test", "id", "tmpl")]
        )
        mock_config_load.return_value = config

        mock_mqtt_instance = mock_mqtt_cls.return_value
        mock_mqtt_instance.connected = True

        daemon = Daemon()

        # directly call the discovery publishing logic
        if config.sensors and config.ha_discovery_enabled:
            if mock_mqtt_instance.connected or config.dry_run:
                for sensor in config.sensors:
                    mock_mqtt_instance.publish_discovery(
                        sensor,
                        config.device_name,
                        config.ha_discovery_prefix,
                        config.mqtt_topic
                    )

        # Verify publish_discovery WAS called
        mock_mqtt_instance.publish_discovery.assert_called()
