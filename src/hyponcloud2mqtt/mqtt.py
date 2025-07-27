"""MQTT client and data publishing module."""

import logging
import json
import ssl
import paho.mqtt.client as mqtt

HA_SENSOR_CONFIG = {
    "today_earning": {"name": "Today's Earning", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "month_earning": {"name": "Month Earning", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "total_earning": {"name": "Total Earning", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "e_total": {"name": "Total Energy", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "e_month": {"name": "Month Energy", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "e_today": {"name": "Today Energy", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "e_year": {"name": "Year Energy", "unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
    "total_tree": {"name": "Total Trees Saved", "icon": "mdi:tree"},
    "total_co2": {"name": "Total CO2 Reduced", "unit_of_measurement": "kg", "icon": "mdi:molecule-co2"},
    "total_diesel": {"name": "Total Diesel Saved", "unit_of_measurement": "L", "icon": "mdi:fuel"},
    "percent": {"name": "Percentage", "unit_of_measurement": "%", "device_class": "power_factor"},
    "meter_power": {"name": "Meter Power", "unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
    "power_load": {"name": "Load Power", "unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
    "w_cha": {"name": "Charge Power", "unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
    "power_pv": {"name": "PV Power", "unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
    "soc": {"name": "State of Charge", "unit_of_measurement": "%", "device_class": "battery", "state_class": "measurement"},
    "micro": {"name": "Micro Inverter Status", "icon": "mdi:solar-panel"},
}

def publish_ha_discovery(client, config, system_id):
    """Publishes Home Assistant MQTT discovery messages."""
    mqtt_config = config.get("mqtt", {})
    base_topic = mqtt_config.get("topic", "hyponcloud2mqtt")
    device_name = f"Hypon Inverter {system_id}"
    device_id = f"hypon_inverter_{system_id}"

    for key, sensor_config in HA_SENSOR_CONFIG.items():
        sensor_name = sensor_config["name"]
        unique_id = f"{device_id}_{key}"
        state_topic = f"{base_topic}/{system_id}"

        payload = {
            "name": sensor_name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "device": {
                "identifiers": [device_id],
                "name": device_name,
                "manufacturer": "Hypon",
                "model": "Inverter",
            },
        }

        if "unit_of_measurement" in sensor_config:
            payload["unit_of_measurement"] = sensor_config["unit_of_measurement"]
        if "device_class" in sensor_config:
            payload["device_class"] = sensor_config["device_class"]
        if "state_class" in sensor_config:
            payload["state_class"] = sensor_config["state_class"]
        if "icon" in sensor_config:
            payload["icon"] = sensor_config["icon"]

        discovery_topic = f"homeassistant/sensor/{device_id}/{key}/config"
        client.publish(discovery_topic, json.dumps(payload), retain=True)
        logging.info(f"Published HA discovery for {sensor_name} to {discovery_topic}")





def connect_mqtt(config):
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
