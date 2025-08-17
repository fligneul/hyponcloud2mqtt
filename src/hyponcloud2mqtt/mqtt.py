"""MQTT client and data publishing module."""

import logging
import json
import ssl
from typing import Dict
import paho.mqtt.client as mqtt


def connect_mqtt(config: Dict):
    """Connects to the MQTT broker."""
    mqtt_config = config.get("mqtt", {})
    client = mqtt.Client()

    # Configure Last Will and Testament (LWT)
    lwt_topic = mqtt_config.get("topic") + "/status"

    if lwt_topic:
        client.will_set(lwt_topic, "offline", retain=True)

    if mqtt_config.get("user"):
        client.username_pw_set(mqtt_config.get("user"), mqtt_config.get("password"))

    # Enable TLS for port 8883
    # if mqtt_config.get("port") == 8883:
    # client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.error("Failed to connect to MQTT broker, return code %s", rc)

    client.on_connect = on_connect

    try:
        client.connect(mqtt_config.get("host"), mqtt_config.get("port", 1883))
        return client
    except Exception as e:
        logging.error("MQTT connection error: %s", e)
        return None


def publish_data(client, config, system_id, data):
    """Publishes data to the MQTT broker."""
    mqtt_config = config.get("mqtt", {})
    base_topic = mqtt_config.get("topic", "hyponcloud2mqtt")
    retain = mqtt_config.get("retain", False)

    # Publish the whole object as JSON
    data_topic = f"{base_topic}/{system_id}"
    client.publish(data_topic, json.dumps(data.__dict__), retain=retain)


def publish_discovery_message(client, config, system_id, data):
    """Publishes Home Assistant discovery messages."""
    mqtt_config = config.get("mqtt", {})
    discovery_config = mqtt_config.get("discovery", {})
    if not discovery_config.get("enabled"):
        return

    discovery_prefix = discovery_config.get("prefix", "homeassistant")
    base_topic = mqtt_config.get("topic", "hyponcloud2mqtt")
    data_topic = f"{base_topic}/{system_id}"
    availability_topic = f"{base_topic}/status"

    device_info = {
        "identifiers": [system_id],
        "name": f"Hypon Inverter {system_id}",
        "manufacturer": "Hypon"
    }

    sensors = {
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

    for key, attributes in sensors.items():
        sensor_name = attributes["name"]
        unique_id = f"hypon_{system_id}_{key}"
        discovery_topic = f"{discovery_prefix}/sensor/{unique_id}/config"
        
        payload = {
            "name": f"{system_id} {sensor_name}",
            "unique_id": unique_id,
            "state_topic": data_topic,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "device": device_info,
            "availability_topic": availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
        }
        
        if "unit" in attributes:
            payload["unit_of_measurement"] = attributes["unit"]
        if "device_class" in attributes:
            payload["device_class"] = attributes["device_class"]
        if "state_class" in attributes:
            payload["state_class"] = attributes["state_class"]
        if "icon" in attributes:
            payload["icon"] = attributes["icon"]
            
        client.publish(discovery_topic, json.dumps(payload), retain=True)

def set_online(client, config):
    """Publishes online status to the MQTT broker."""
    mqtt_config = config.get("mqtt", {})
    lwt_topic = mqtt_config.get("topic") + "/status"
    client.publish(lwt_topic, "online", retain=True)


def disconnect_mqtt(client):
    """Disconnects from the MQTT broker."""
    client.disconnect()
    logging.info("Disconnected from MQTT broker.")