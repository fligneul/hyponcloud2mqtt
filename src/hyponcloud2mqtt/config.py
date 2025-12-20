from __future__ import annotations
import os
import logging
from dataclasses import dataclass
from typing import List, Any

logger = logging.getLogger(__name__)


@dataclass
class Config:
    http_url: str
    system_ids: List[str]
    http_interval: int
    mqtt_broker: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_availability_topic: str
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    api_username: str | None = None
    api_password: str | None = None
    verify_ssl: bool = True
    mqtt_tls_enabled: bool = False
    mqtt_tls_insecure: bool = False
    mqtt_ca_path: str | None = None
    dry_run: bool = False
    ha_discovery_enabled: bool = True
    ha_discovery_prefix: str = "homeassistant"
    device_name: str = "hyponcloud2mqtt"
    health_server_enabled: bool = True
    mqtt_client_id: str = "hyponcloud2mqtt"

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":  # noqa: C901
        # Defaults
        config: dict[str, Any] = {
            "http_url": "https://127.0.0.1:8080",
            "system_ids": [],  # Required, no default
            "http_interval": 60,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_topic": "home/data",
            # Will default to {mqtt_topic}/status
            "mqtt_availability_topic": None,
            "mqtt_username": None,
            "mqtt_password": None,
            "mqtt_tls_enabled": False,
            "mqtt_tls_insecure": False,
            "mqtt_ca_path": None,
            "api_username": None,
            "api_password": None,
            "verify_ssl": True,
            "dry_run": False,
            "ha_discovery_enabled": True,
            "ha_discovery_prefix": "homeassistant",
            "device_name": "hyponcloud2mqtt",
            "mqtt_client_id": "hyponcloud2mqtt",
        }

        # Load from file if exists
        if config_path and os.path.exists(config_path):
            import yaml
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config.update(file_config)
            except Exception as e:
                logger.warning(f"Error loading config file {config_path}: {e}")
        else:
            if config_path:
                logger.info(
                    f"Config file {config_path} not found, using defaults")
            else:
                logger.info(
                    "No config file specified, using defaults and environment variables")

        # Override with Env Vars (Env > File > Defaults)
        if os.getenv("HTTP_URL"):
            config["http_url"] = os.getenv("HTTP_URL")

        # Env Var for system_ids (comma-separated)
        system_ids_env = os.getenv("SYSTEM_IDS")
        if system_ids_env:
            config["system_ids"] = [s.strip()
                                    for s in system_ids_env.split(',') if s.strip()]

        http_interval_env = os.getenv("HTTP_INTERVAL")
        if http_interval_env:
            try:
                config["http_interval"] = int(http_interval_env)
            except ValueError:
                pass

        if os.getenv("MQTT_BROKER"):
            config["mqtt_broker"] = os.getenv("MQTT_BROKER")

        mqtt_port_env = os.getenv("MQTT_PORT")
        if mqtt_port_env:
            try:
                config["mqtt_port"] = int(mqtt_port_env)
            except ValueError:
                pass

        if os.getenv("MQTT_TOPIC"):
            config["mqtt_topic"] = os.getenv("MQTT_TOPIC")

        mqtt_availability_topic_env = os.getenv("MQTT_AVAILABILITY_TOPIC")
        if mqtt_availability_topic_env:
            config["mqtt_availability_topic"] = mqtt_availability_topic_env

        # Default availability topic if not set
        if not config.get("mqtt_availability_topic"):
            config["mqtt_availability_topic"] = f"{config['mqtt_topic']}/status"

        if os.getenv("MQTT_USERNAME"):
            config["mqtt_username"] = os.getenv("MQTT_USERNAME")

        if os.getenv("MQTT_PASSWORD"):
            config["mqtt_password"] = os.getenv("MQTT_PASSWORD")

        if os.getenv("MQTT_CLIENT_ID"):
            config["mqtt_client_id"] = os.getenv("MQTT_CLIENT_ID")

        mqtt_tls_enabled_env = os.getenv("MQTT_TLS_ENABLED")
        if mqtt_tls_enabled_env:
            config["mqtt_tls_enabled"] = mqtt_tls_enabled_env.lower() in ("true", "1", "yes")

        mqtt_tls_insecure_env = os.getenv("MQTT_TLS_INSECURE")
        if mqtt_tls_insecure_env:
            config["mqtt_tls_insecure"] = mqtt_tls_insecure_env.lower() in ("true", "1", "yes")

        if os.getenv("MQTT_CA_PATH"):
            config["mqtt_ca_path"] = os.getenv("MQTT_CA_PATH")

        if os.getenv("API_USERNAME"):
            config["api_username"] = os.getenv("API_USERNAME")

        if os.getenv("API_PASSWORD"):
            config["api_password"] = os.getenv("API_PASSWORD")

        if os.getenv("HA_DISCOVERY_PREFIX"):
            config["ha_discovery_prefix"] = os.getenv("HA_DISCOVERY_PREFIX")

        if os.getenv("DEVICE_NAME"):
            config["device_name"] = os.getenv("DEVICE_NAME")

        verify_ssl_env = os.getenv("VERIFY_SSL")
        if verify_ssl_env:
            config["verify_ssl"] = verify_ssl_env.lower() in ("true", "1", "yes")

        dry_run_env = os.getenv("DRY_RUN")
        if dry_run_env:
            config["dry_run"] = dry_run_env.lower() in ("true", "1", "yes")

        ha_discovery_enabled_env = os.getenv("HA_DISCOVERY_ENABLED")
        if ha_discovery_enabled_env:
            config["ha_discovery_enabled"] = ha_discovery_enabled_env.lower() in ("true", "1", "yes")

        # Validate configuration
        cls._validate_config(config)

        logger.info(
            f"Configuration loaded: {config['http_url']} -> {config['mqtt_topic']}")
        logger.info(
            f"SSL verification: {'enabled' if config['verify_ssl'] else 'disabled'}")
        if config['dry_run']:
            logger.warning(
                "DRY RUN MODE: MQTT publishing disabled (logging only)")

        return cls(**config)

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:  # noqa: C901
        """Validate configuration values for security and correctness."""
        # Validate HTTP URL
        http_url = config.get("http_url", "")
        if not http_url:
            raise ValueError("http_url is required")
        if not http_url.startswith(("http://", "https://")):
            raise ValueError(
                f"http_url must start with http:// or https://, got: {http_url}")

        # Validate system_ids
        system_ids = config.get("system_ids", [])
        if not isinstance(system_ids, list) or not system_ids:
            raise ValueError("system_ids must be a non-empty list")

        # Ensure all IDs are strings
        if not all(isinstance(s, str) for s in system_ids):
            raise ValueError("All elements in system_ids must be strings")

        # Validate HTTP interval
        http_interval = config.get("http_interval", 0)
        if http_interval <= 0:
            raise ValueError(
                f"http_interval must be positive, got: {http_interval}")
        if http_interval > 86400:  # 24 hours
            logger.warning(
                f"http_interval is very large ({http_interval}s), consider reducing it")

        # Validate MQTT port
        mqtt_port = config.get("mqtt_port", 0)
        if not (1 <= mqtt_port <= 65535):
            raise ValueError(
                f"mqtt_port must be between 1 and 65535, got: {mqtt_port}")

        # Validate MQTT topic
        mqtt_topic = config.get("mqtt_topic", "")
        if not mqtt_topic:
            raise ValueError("mqtt_topic is required")
        if mqtt_topic.startswith("$"):
            raise ValueError(
                "mqtt_topic cannot start with $ (reserved for MQTT system topics)")

        # Security warnings
        if not config.get("verify_ssl"):
            logger.warning(
                "SSL verification is DISABLED - this is insecure and should only be used for testing")

        if config.get("mqtt_tls_insecure"):
            logger.warning(
                "MQTT TLS verification is DISABLED - this is insecure and should only be used for testing")

        # Validate MQTT credentials consistency
        mqtt_username = config.get("mqtt_username")
        mqtt_password = config.get("mqtt_password")
        if mqtt_username and not mqtt_password:
            logger.warning(
                "MQTT username provided without password - authentication may fail")
        if mqtt_password and not mqtt_username:
            logger.warning(
                "MQTT password provided without username - authentication may fail")
