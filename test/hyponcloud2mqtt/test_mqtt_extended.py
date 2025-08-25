import pytest
from unittest.mock import patch, MagicMock
from src.hyponcloud2mqtt.mqtt import set_online, disconnect_mqtt, publish_discovery_message
from src.hyponcloud2mqtt.hypon_cloud import MonitorData
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
            "discovery": {
                "enabled": True,
                "prefix": "homeassistant"
            }
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
        micro=2,
    )

def test_set_online(mock_config, mock_mqtt_client):
    set_online(mock_mqtt_client, mock_config)
    mock_mqtt_client.publish.assert_called_once_with(
        "test/hypon/status", "online", retain=True
    )

def test_disconnect_mqtt(mock_mqtt_client):
    disconnect_mqtt(mock_mqtt_client)
    mock_mqtt_client.disconnect.assert_called_once()

def test_publish_discovery_message_all_sensors(mock_config, mock_mqtt_client, mock_monitor_data):
    publish_discovery_message(mock_mqtt_client, mock_config, "test_system_id", mock_monitor_data)

    # Expected number of sensors
    assert mock_mqtt_client.publish.call_count == 17

    expected_sensors = {
        "today_earning": {"name": "Today Earning", "icon": "mdi:currency"},
        "month_earning": {"name": "Month Earning", "icon": "mdi:currency"},
        "total_earning": {"name": "Total Earning", "icon": "mdi:currency"},
        "e_total": {"name": "Total Energy", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing"},
        "e_month": {"name": "Month Energy", "unit": "kWh", "device_class": "energy"},
        "e_today": {"name": "Today Energy", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing"},
        "e_year": {"name": "Year Energy", "unit": "kWh", "device_class": "energy"},
        "total_tree": {"name": "Trees Planted", "unit": "trees", "icon": "mdi:tree"},
        "total_co2": {"name": "CO2 Saved", "unit": "kg", "icon": "mdi:molecule-co2"},
        "total_diesel": {"name": "Diesel Saved", "unit": "L", "icon": "mdi:barrel"},
        "percent": {"name": "Capacity Percentage", "unit": "%", "icon": "mdi:percent"},
        "meter_power": {"name": "Meter Power", "unit": "W", "device_class": "power"},
        "power_load": {"name": "Power Load", "unit": "W", "device_class": "power"},
        "w_cha": {"name": "Charging Power", "unit": "W", "device_class": "power"},
        "power_pv": {"name": "PV Power", "unit": "W", "device_class": "power"},
        "soc": {"name": "State of Charge", "unit": "%", "device_class": "battery"},
        "micro": {"name": "Microinverters", "icon": "mdi:chip"},
    }

    # Check the payload for each sensor
    for call in mock_mqtt_client.publish.call_args_list:
        topic = call[0][0]
        payload = json.loads(call[0][1])
        sensor_key = topic.split("/")[-2].replace("hypon_test_system_id_", "")

        assert topic.startswith("homeassistant/sensor/hypon_test_system_id_")
        assert payload["device"]["identifiers"] == ["test_system_id"]
        assert payload["availability_topic"] == "test/hypon/status"

        expected = expected_sensors[sensor_key]
        assert payload["name"] == f"test_system_id {expected['name']}"
        if "unit" in expected:
            assert payload["unit_of_measurement"] == expected["unit"]
        if "device_class" in expected:
            assert payload["device_class"] == expected["device_class"]
        if "state_class" in expected:
            assert payload["state_class"] == expected["state_class"]
        if "icon" in expected:
            assert payload["icon"] == expected["icon"]
