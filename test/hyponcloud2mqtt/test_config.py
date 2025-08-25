import pytest
from unittest.mock import mock_open, patch
from src.hyponcloud2mqtt.config import load_config

def test_load_config_success():
    mock_yaml_content = """
hypon:
  user: "test_user"
  password: "test_password"
mqtt:
  host: "test_host"
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        with patch("yaml.safe_load", return_value={"hypon": {"user": "test_user", "password": "test_password"}, "mqtt": {"host": "test_host"}}):
            config = load_config()
            assert config == {
                "hypon": {
                    "user": "test_user",
                    "password": "test_password",
                    "api_base_url": "https://api.hypon.cloud/v2",
                    "system_ids": ["YOUR_SYSTEM_ID"],
                    "interval": 60,
                    "retries": 0,
                },
                "mqtt": {
                    "host": "test_host",
                    "port": 1883,
                    "user": "",
                    "password": "",
                    "topic": "hyponcloud2mqtt",
                    "retain": False,
                    "ssl": False,
                },
            }

def test_load_config_with_env_override():
    mock_yaml_content = """
hypon:
  user: "yaml_user"
  password: "yaml_password"
mqtt:
  host: "yaml_host"
  port: 1883
  ssl: false
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        with patch("yaml.safe_load", return_value={"hypon": {"user": "yaml_user", "password": "yaml_password"}, "mqtt": {"host": "yaml_host", "port": 1883, "ssl": False}}):
            with patch.dict("os.environ", {
                "HYPON_USER": "env_user",
                "MQTT_HOST": "env_host",
                "MQTT_PORT": "8883",
                "MQTT_SSL": "true"
            }):
                config = load_config()
                assert config["hypon"]["user"] == "env_user"
                assert config["hypon"]["password"] == "yaml_password"
                assert config["mqtt"]["host"] == "env_host"
                assert config["mqtt"]["port"] == 8883
                assert config["mqtt"]["ssl"] is True

def test_load_config_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = load_config()
        assert config is not None

def test_load_config_invalid_yaml():
    mock_yaml_content = """
hypon:
  user: "test_user"
  password: "test_password"
mqtt:
  host: "test_host"
    invalid_line
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        with patch("yaml.safe_load", side_effect=Exception("YAML parsing error")):
            with pytest.raises(Exception, match="YAML parsing error"):
                load_config()
