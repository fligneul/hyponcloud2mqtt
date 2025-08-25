import pytest
from unittest.mock import patch, MagicMock
from src.hyponcloud2mqtt.mqtt import connect_mqtt, publish_data
from src.hyponcloud2mqtt.hypon_cloud import MonitorData
import paho.mqtt.client as mqtt
import json


@pytest.fixture
def mock_config():
    return {
        "mqtt": {
            "host": "test_mqtt_host",
            "port": 1883,
            "user": "test_user",
            "password": "test_password",
            "topic": "test/hypon",
            "retain": False,
            "dry_run": False,
        }
    }


@pytest.fixture
def mock_mqtt_client():
    with patch("paho.mqtt.client.Client") as MockClient:
        instance = MockClient.return_value
        yield instance


@pytest.fixture
def mock_monitor_data():
    return MonitorData(
        monetary="USD",
        today_earning=10.0,
        month_earning=100.0,
        total_earning=1000.0,
        e_total=5000.0,
        e_month=500.0,
        e_today=50.0,
        e_year=2000.0,
        total_tree=5,
        total_co2=10,
        total_diesel=20,
        percent=90.0,
        meter_power=5.0,
        power_load=2.0,
        w_cha=1.0,
        power_pv=3.0,
        soc=80.0,
        micro=0.5,
    )


def test_connect_mqtt_success(mock_config, mock_mqtt_client):
    client = connect_mqtt(mock_config)
    mock_mqtt_client.username_pw_set.assert_called_once_with(
        "test_user", "test_password"
    )
    mock_mqtt_client.connect.assert_called_once_with("test_mqtt_host", 1883)
    assert client == mock_mqtt_client


def test_connect_mqtt_no_auth(mock_config, mock_mqtt_client):
    mock_config["mqtt"].pop("user")
    mock_config["mqtt"].pop("password")
    client = connect_mqtt(mock_config)
    mock_mqtt_client.username_pw_set.assert_not_called()
    mock_mqtt_client.connect.assert_called_once_with("test_mqtt_host", 1883)
    assert client == mock_mqtt_client


def test_publish_data(mock_config, mock_mqtt_client, mock_monitor_data):
    publish_data(mock_mqtt_client, mock_config, "test_system_id", mock_monitor_data)
    expected_topic = "test/hypon/data/test_system_id"
    expected_payload = json.dumps(mock_monitor_data.__dict__)
    mock_mqtt_client.publish.assert_called_once_with(
        expected_topic, expected_payload, retain=False
    )


def test_publish_data_retain_true(mock_config, mock_mqtt_client, mock_monitor_data):
    mock_config["mqtt"]["retain"] = True
    publish_data(mock_mqtt_client, mock_config, "test_system_id", mock_monitor_data)
    expected_topic = "test/hypon/data/test_system_id"
    expected_payload = json.dumps(mock_monitor_data.__dict__)
    mock_mqtt_client.publish.assert_called_once_with(
        expected_topic, expected_payload, retain=True
    )


def test_connect_mqtt_with_lwt(mock_config, mock_mqtt_client):
    client = connect_mqtt(mock_config)

    mock_mqtt_client.will_set.assert_called_once_with(
        "test/hypon/status", "offline", retain=True
    )
    mock_mqtt_client.connect.assert_called_once_with("test_mqtt_host", 1883)
    assert client == mock_mqtt_client
