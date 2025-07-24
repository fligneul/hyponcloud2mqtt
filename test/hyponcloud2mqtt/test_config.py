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
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)) as mock_file:
        with patch(
            "yaml.safe_load",
            return_value={
                "hypon": {"user": "test_user", "password": "test_password"},
                "mqtt": {"host": "test_host"},
            },
        ) as mock_safe_load:
            config = load_config()
            mock_file.assert_called_once_with("config.yaml", "r", encoding="utf-8")
            mock_safe_load.assert_called_once_with(mock_file())
            assert config == {
                "hypon": {"user": "test_user", "password": "test_password"},
                "mqtt": {"host": "test_host"},
            }


def test_load_config_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_config()


def test_load_config_invalid_yaml():
    mock_yaml_content = """
hypon:
  user: "test_user"
  password: "test_password"
mqtt:
  host: "test_host"
    invalid_line
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)) as mock_file:
        with patch("yaml.safe_load", side_effect=Exception("YAML parsing error")):
            with pytest.raises(Exception, match="YAML parsing error"):
                load_config()
