"""MQTT client and data publishing module."""

import logging
import json
import ssl
import paho.mqtt.client as mqtt


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

    if mqtt_config.get("ssl"):
        client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)

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
