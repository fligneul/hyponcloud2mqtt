from __future__ import annotations
import json
import logging
import threading
import paho.mqtt.client as mqtt
from typing import Any

logger = logging.getLogger(__name__)


class MqttClient:
    def __init__(
            self,
            broker: str,
            port: int,
            topic: str,
            availability_topic: str,
            username: str | None = None,
            password: str | None = None,
            dry_run: bool = False,
            tls_enabled: bool = False,
            tls_insecure: bool = False,
            ca_path: str | None = None,
            client_id: str | None = None):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.availability_topic = availability_topic
        self.dry_run = dry_run
        self.connected = False
        self._connection_event = threading.Event()
        self._connection_result = None
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id
        )

        if username and password:
            self.client.username_pw_set(username, password)
            logger.debug(
                f"MQTT authentication configured for user: {username}")

        if tls_enabled:
            # Enable TLS
            # If ca_path is None, it uses system default CAs
            self.client.tls_set(ca_certs=ca_path)

            if tls_insecure:
                self.client.tls_insecure_set(True)

            logger.debug(f"MQTT TLS enabled (insecure: {tls_insecure})")

        # Set LWT
        self.client.will_set(self.availability_topic, "offline", retain=True)
        logger.debug(
            f"MQTT Last Will and Testament set to {availability_topic}")

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(
                f"Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
            # Publish online status
            self.client.publish(self.availability_topic, "online", retain=True)
            logger.debug(f"Published 'online' to {self.availability_topic}")
        else:
            self.connected = False
            error_msg = f"Failed to connect to MQTT broker, reason: {rc}"

            # Troubleshooting tips based on Paho ReasonCode (supports int and string)
            # rc 5 is 'Not authorized' in MQTT v3.1.1, 135 in MQTT v5
            rc_str = str(rc)
            if rc_str == "Not authorized" or rc == 5 or rc == 135:
                error_msg += "\n[TIP] 'Not authorized' typically means:"
                error_msg += "\n      - Incorrect MQTT_USERNAME or MQTT_PASSWORD"
                error_msg += "\n      - The user does not have permission to use the Client ID provided"
                error_msg += "\n      - The user does not have permission to publish/subscribe to the topics"
            elif rc_str == "Bad user name or password" or rc == 4 or rc == 134:
                error_msg += "\n[TIP] 'Bad user name or password': Double-check MQTT_USERNAME and MQTT_PASSWORD."
            elif rc_str == "Connection refused" or rc == 1 or rc == 128:
                error_msg += "\n[TIP] 'Connection refused': Check MQTT_BROKER address, MQTT_PORT, and firewall settings."

            logger.error(error_msg)

        # Signal connection attempt completed
        self._connection_result = rc
        self._connection_event.set()

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self.connected = False
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")

    def connect(self, timeout: int = 10) -> bool:
        """Connect to MQTT broker and wait for connection to succeed or fail.

        Args:
            timeout: Maximum seconds to wait for connection (default: 10)

        Returns:
            True if connected successfully, False otherwise
        """
        logger.info(
            f"Connecting to MQTT broker at {self.broker}:{self.port}...")

        # Reset connection event
        self._connection_event.clear()
        self._connection_result = None

        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logger.debug("MQTT client loop started")
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False

        # Wait for connection callback
        if self._connection_event.wait(timeout):
            # Connection attempt completed
            if self._connection_result == 0:
                return True
            else:
                logger.error(
                    f"MQTT connection failed with code {self._connection_result}")
                return False
        else:
            logger.error(f"MQTT connection timeout after {timeout} seconds")
            return False

    def disconnect(self):
        if not self.dry_run and self.connected:
            try:
                logger.debug(
                    f"Publishing 'offline' to {self.availability_topic}")
                info = self.client.publish(
                    self.availability_topic, "offline", retain=True)
                # Wait for the message to be published (with timeout to not
                # block shutdown)
                info.wait_for_publish(timeout=2.0)
                logger.debug("Offline status published successfully")
            except Exception as e:
                logger.warning(f"Failed to publish offline status: {e}")

        logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        logger.debug("MQTT client disconnected")

    def publish(self, data: Any, topic: str | None = None, retain: bool = False):
        """Publish data to a specific topic, or the default if not provided."""
        publish_topic = topic if topic is not None else self.topic

        if self.dry_run:
            payload = json.dumps(data, indent=2)
            logger.info(
                f"[DRY RUN] Would publish to {publish_topic} (retain={retain}):\n{payload}")
            return

        try:
            payload = json.dumps(data)
            logger.debug(
                f"Publishing {len(payload)} bytes to {publish_topic}, retain={retain}")
            info = self.client.publish(publish_topic, payload, retain=retain)
            info.wait_for_publish()
            logger.debug(
                f"Data published successfully to {publish_topic}")
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
