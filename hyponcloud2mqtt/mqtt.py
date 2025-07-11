"""MQTT client and data publishing module."""
import logging
import json
import paho.mqtt.client as mqtt

def connect_mqtt(config):
    """Connects to the MQTT broker."""
    mqtt_config = config.get("mqtt", {})
    client = mqtt.Client()
    if mqtt_config.get("user"):
        client.username_pw_set(mqtt_config.get("user"), mqtt_config.get("password"))
    client.connect(mqtt_config.get("host"), mqtt_config.get("port", 1883))
    return client

def publish_data(client, config, system_id, data):
    """Publishes data to the MQTT broker."""
    mqtt_config = config.get("mqtt", {})
    base_topic = mqtt_config.get("topic", "hyponcloud2mqtt")
    retain = mqtt_config.get("retain", False)
    dry_run = mqtt_config.get("dry_run", True) # Default to True

    publish_mode = mqtt_config.get("publish_mode", "full") # Default to full

    if dry_run:
        logging.info("Dry run: MQTT publishing is disabled. Data would have been published.")
        if publish_mode == "full":
            full_topic = f"{base_topic}/{system_id}/full_data"
            logging.info("Dry run: Full JSON data to topic '%s': %s", full_topic, json.dumps(data.__dict__))
        elif publish_mode == "individual":
            for key, value in data.__dict__.items():
                topic = f"{base_topic}/{system_id}/{key}"
                logging.info("Dry run: Individual data to topic '%s': %s", topic, str(value))
        return

    if publish_mode == "full":
        # Publish the whole object as JSON
        full_topic = f"{base_topic}/{system_id}/full_data"
        client.publish(full_topic, json.dumps(data.__dict__), retain=retain)
    elif publish_mode == "individual":
        # Publish each attribute as a separate topic
        for key, value in data.__dict__.items():
            topic = f"{base_topic}/{system_id}/{key}"
            client.publish(topic, str(value), retain=retain)
    else:
        # Fallback or log a warning if an unknown mode is configured
        logging.warning("Unknown MQTT publish_mode '%s'. Defaulting to full.", publish_mode)
        full_topic = f"{base_topic}/{system_id}/full_data"
        client.publish(full_topic, json.dumps(data.__dict__), retain=retain)
