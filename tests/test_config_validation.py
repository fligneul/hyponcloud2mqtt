import pytest
from hyponcloud2mqtt.config import Config


def test_validation_invalid_http_url(monkeypatch):
    """Test that invalid HTTP URLs are rejected"""
    import os
    monkeypatch.setenv("SYSTEM_IDS", "12345")
    os.environ["HTTP_URL"] = "ftp://invalid.com"
    with pytest.raises(ValueError, match="http_url must start with http"):
        Config.load()
    del os.environ["HTTP_URL"]


def test_validation_negative_interval(monkeypatch):
    """Test that negative intervals are rejected"""
    import os
    monkeypatch.setenv("SYSTEM_IDS", "12345")
    os.environ["HTTP_INTERVAL"] = "-10"
    with pytest.raises(ValueError, match="http_interval must be positive"):
        Config.load()
    del os.environ["HTTP_INTERVAL"]


def test_validation_invalid_mqtt_port(monkeypatch):
    """Test that invalid MQTT ports are rejected"""
    import os
    monkeypatch.setenv("SYSTEM_IDS", "12345")
    os.environ["MQTT_PORT"] = "99999"
    with pytest.raises(ValueError, match="mqtt_port must be between"):
        Config.load()
    del os.environ["MQTT_PORT"]


def test_validation_mqtt_system_topic(monkeypatch):
    """Test that MQTT system topics are rejected"""
    import os
    monkeypatch.setenv("SYSTEM_IDS", "12345")
    os.environ["MQTT_TOPIC"] = "$SYS/test"
    with pytest.raises(ValueError, match="cannot start with"):
        Config.load()
    del os.environ["MQTT_TOPIC"]


def test_validation_valid_config(monkeypatch):
    """Test that valid configuration passes validation"""
    import os
    monkeypatch.setenv("SYSTEM_IDS", "12345")
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


def test_system_ids_from_env_var():
    """Test that SYSTEM_ID env var is parsed correctly"""
    import os
    os.environ["SYSTEM_IDS"] = "123, 456, 789"
    config = Config.load()
    assert config.system_ids == ["123", "456", "789"]
    del os.environ["SYSTEM_IDS"]


def test_empty_system_ids_raises_error(monkeypatch):
    """Test that validation fails if system_ids is empty"""
    # Ensure SYSTEM_ID is not set
    monkeypatch.delenv("SYSTEM_IDS", raising=False)
    with pytest.raises(ValueError, match="system_ids must be a non-empty list"):
        Config.load()
