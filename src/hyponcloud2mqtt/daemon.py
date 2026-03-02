from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time

from .config import Config
from .data_fetcher import DataFetcher
from .discovery import publish_discovery_message
from .health_server import HealthContext, HealthHTTPHandler, HealthServer
from .mqtt_client import MqttClient

logger = logging.getLogger(__name__)


class Daemon:
    def __init__(self, config: Config | None = None):
        self.running = True
        self.config = config
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info("Received signal %s, stopping...", signum)
        self.running = False

    def _connect_mqtt_with_backoff(self, mqtt_client: MqttClient) -> bool:
        """
        Connects to MQTT broker with exponential backoff.
        Returns True if connected, False if daemon is stopping.
        """
        retry_delay = 5
        max_retry_delay = 60

        while self.running:
            # If already connected (or paho handles it), this check is good,
            # but MqttClient.connect usually triggers the connection attempt.
            # Assuming MqttClient.connect returns success boolean.
            if mqtt_client.connect(timeout=10):
                logger.info("Connected to MQTT broker")
                return True

            logger.warning("MQTT connection failed, retrying in %s seconds...", retry_delay)

            # Sleep in short intervals to respond to signals
            for _ in range(retry_delay):
                if not self.running:
                    return False
                time.sleep(1)

            retry_delay = min(retry_delay * 2, max_retry_delay)

        return False

    def run(self):  # noqa: C901
        if self.config:
            config = self.config
        else:
            config_path = os.getenv("CONFIG_FILE", "config.yaml")
            try:
                config = Config.load(config_path)
            except Exception as e:
                logger.critical("Configuration error: %s", e)
                sys.exit(1)

        mqtt_client = MqttClient(
            config.mqtt_broker,
            config.mqtt_port,
            config.mqtt_topic,
            config.mqtt_availability_topic,
            config.mqtt_username,
            config.mqtt_password,
            config.dry_run,
            config.mqtt_tls_enabled,
            config.mqtt_tls_insecure,
            config.mqtt_ca_path,
            config.mqtt_client_id,
        )

        # Start Health Server
        if config.health_server_enabled:
            health_context = HealthContext(mqtt_client)
            health_server = HealthServer(("0.0.0.0", 8080), HealthHTTPHandler, health_context)
            health_thread = threading.Thread(target=health_server.serve_forever, daemon=True)
            health_thread.start()
            logger.info("Health check server started on port 8080")

        # Initial MQTT connection
        if not config.dry_run:
            if not self._connect_mqtt_with_backoff(mqtt_client) and not self.running:
                # Daemon stopping received during initial connection attempt
                logger.info("Stopping before MQTT connection established")
                sys.exit(0)
        else:
            logger.info("[DRY RUN] Skipping MQTT connection")

        # Publish HA Discovery (only if MQTT is connected)
        if config.ha_discovery_enabled:
            # Check connection status directly from client or assume connected if not dry_run succeeded
            if mqtt_client.connected:
                logger.info("Publishing Home Assistant discovery messages...")
                for system_id in config.system_ids:
                    publish_discovery_message(mqtt_client, config, system_id)
            elif not config.dry_run:
                # Should not happen if _connect_mqtt_with_backoff returned True
                logger.warning("Skipping Home Assistant discovery: MQTT not connected")

        # Initialize Data Fetchers for each system ID
        data_fetchers = [DataFetcher(config, system_id) for system_id in config.system_ids]
        logger.info("Initialized %s data fetchers for system IDs: %s", len(data_fetchers), config.system_ids)

        logger.info("Starting daemon, fetching every %s seconds", config.http_interval)

        while self.running:
            # Check MQTT connection before fetching (unless in dry run mode)
            if not config.dry_run and not mqtt_client.connected:
                logger.warning("MQTT disconnected, attempting to reconnect...")
                if not self._connect_mqtt_with_backoff(mqtt_client):
                    break

            logger.debug("Starting fetch cycle (interval: %ss)", config.http_interval)

            for fetcher in data_fetchers:
                if not self.running:
                    break

                system_id = fetcher.system_id
                logger.debug("Fetching data for system_id: %s", system_id)

                # Fetch and Merge Data
                merged_data = fetcher.fetch_all()

                # Construct topic for this system_id
                system_topic = f"{config.mqtt_topic}/{system_id}"

                if merged_data:
                    logger.debug("Publishing merged data for %s to %s", system_id, system_topic)
                    mqtt_client.publish(merged_data, topic=system_topic)
                    logger.info("Data for %s published successfully", system_id)
                else:
                    logger.warning("No data to publish for system_id: %s (endpoints failed or returned empty)", system_id)

            # Sleep in short intervals to respond to signals faster
            for _ in range(config.http_interval):
                if not self.running:
                    break
                time.sleep(1)

        mqtt_client.disconnect()
        logger.info("Daemon stopped")
