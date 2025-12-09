import pytest
from hyponcloud2mqtt.config import Config


def test_validation_invalid_http_url():
    """Test that invalid HTTP URLs are rejected"""
    import os
    os.environ["HTTP_URL"] = "ftp://invalid.com"
    with pytest.raises(ValueError, match="http_url must start with http"):
        Config.load()
    del os.environ["HTTP_URL"]


def test_validation_negative_interval():
    """Test that negative intervals are rejected"""
    import os
    os.environ["HTTP_INTERVAL"] = "-10"
    with pytest.raises(ValueError, match="http_interval must be positive"):
        Config.load()
    del os.environ["HTTP_INTERVAL"]


def test_validation_invalid_mqtt_port():
    """Test that invalid MQTT ports are rejected"""
    import os
    os.environ["MQTT_PORT"] = "99999"
    with pytest.raises(ValueError, match="mqtt_port must be between"):
        Config.load()
    del os.environ["MQTT_PORT"]


def test_validation_mqtt_system_topic():
    """Test that MQTT system topics are rejected"""
    import os
    os.environ["MQTT_TOPIC"] = "$SYS/test"
    with pytest.raises(ValueError, match="cannot start with"):
        Config.load()
    del os.environ["MQTT_TOPIC"]


def test_validation_valid_config():
    """Test that valid configuration passes validation"""
    import os
    os.environ["HTTP_URL"] = "http://valid.com"
    os.environ["HTTP_INTERVAL"] = "60"
    os.environ["MQTT_PORT"] = "1883"
    os.environ["MQTT_TOPIC"] = "valid/topic"

    config = Config.load()
    assert config.http_url == "http://valid.com"
    assert config.http_interval == 60
    assert config.mqtt_port == 1883
    assert config.mqtt_topic == "valid/topic"

    # Cleanup
    del os.environ["HTTP_URL"]
    del os.environ["HTTP_INTERVAL"]
    del os.environ["MQTT_PORT"]
    del os.environ["MQTT_TOPIC"]
