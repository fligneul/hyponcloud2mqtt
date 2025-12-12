from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class SensorConfig:
    name: str
    unique_id: str
    value_template: str
    device_class: str | None = None
    unit_of_measurement: str | None = None


@dataclass
class Config:
    http_url: str
    system_id: str
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
    ha_discovery_enabled: bool = False
    ha_discovery_prefix: str = "homeassistant"
    device_name: str = "hyponcloud2mqtt"
    sensors: List[SensorConfig] = field(default_factory=list)

    def __repr__(self) -> str:
        # Redact sensitive fields for logging
        redacted_fields = self.__dict__.copy()
        if 'api_password' in redacted_fields:
            redacted_fields['api_password'] = '********'
        if 'mqtt_password' in redacted_fields:
            redacted_fields['mqtt_password'] = '********'

        fields_str = ', '.join(
            f"{k}={v!r}" for k, v in redacted_fields.items())
        return f"Config({fields_str})"

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        # Defaults
        config = {
            "http_url": "https://httpbin.org/get",  # Dummy URL as requested
            "system_id": "",  # Required, no default
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
            "ha_discovery_enabled": False,
            "ha_discovery_prefix": "homeassistant",
            "device_name": "hyponcloud2mqtt",
            "sensors": [],
        }
        logger.debug(f"Initial default config: {config}")

        # Load from file if exists
        if config_path and os.path.exists(config_path):
            import yaml
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        logger.debug(
                            f"Updating config from file: {config_path}")
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
        env_overrides = {}
        if os.getenv("HTTP_URL"):
            env_overrides["http_url"] = os.getenv("HTTP_URL")

        if os.getenv("SYSTEM_ID"):
            env_overrides["system_id"] = os.getenv("SYSTEM_ID")

        if os.getenv("HTTP_INTERVAL"):
            try:
                env_overrides["http_interval"] = int(
                    os.getenv("HTTP_INTERVAL"))
            except ValueError:
                pass

        if os.getenv("MQTT_BROKER"):
            env_overrides["mqtt_broker"] = os.getenv("MQTT_BROKER")

        if os.getenv("MQTT_PORT"):
            try:
                env_overrides["mqtt_port"] = int(os.getenv("MQTT_PORT"))
            except ValueError:
                pass

        if os.getenv("MQTT_TOPIC"):
            env_overrides["mqtt_topic"] = os.getenv("MQTT_TOPIC")

        if os.getenv("MQTT_AVAILABILITY_TOPIC"):
            env_overrides["mqtt_availability_topic"] = os.getenv(
                "MQTT_AVAILABILITY_TOPIC")

        if os.getenv("MQTT_USERNAME"):
            env_overrides["mqtt_username"] = os.getenv("MQTT_USERNAME")

        if os.getenv("MQTT_PASSWORD"):
            env_overrides["mqtt_password"] = os.getenv("MQTT_PASSWORD")

        if os.getenv("MQTT_TLS_ENABLED"):
            env_overrides["mqtt_tls_enabled"] = os.getenv(
                "MQTT_TLS_ENABLED").lower() in ("true", "1", "yes")

        if os.getenv("MQTT_TLS_INSECURE"):
            env_overrides["mqtt_tls_insecure"] = os.getenv(
                "MQTT_TLS_INSECURE").lower() in ("true", "1", "yes")

        if os.getenv("MQTT_CA_PATH"):
            env_overrides["mqtt_ca_path"] = os.getenv("MQTT_CA_PATH")

        if os.getenv("API_USERNAME"):
            env_overrides["api_username"] = os.getenv("API_USERNAME")

        if os.getenv("API_PASSWORD"):
            env_overrides["api_password"] = os.getenv("API_PASSWORD")

        if os.getenv("HA_DISCOVERY_PREFIX"):
            env_overrides["ha_discovery_prefix"] = os.getenv(
                "HA_DISCOVERY_PREFIX")

        if os.getenv("DEVICE_NAME"):
            env_overrides["device_name"] = os.getenv("DEVICE_NAME")

        if os.getenv("VERIFY_SSL"):
            env_overrides["verify_ssl"] = os.getenv(
                "VERIFY_SSL").lower() in ("true", "1", "yes")

        if os.getenv("DRY_RUN"):
            env_overrides["dry_run"] = os.getenv(
                "DRY_RUN").lower() in ("true", "1", "yes")

        if os.getenv("HA_DISCOVERY_ENABLED"):
            env_overrides["ha_discovery_enabled"] = os.getenv(
                "HA_DISCOVERY_ENABLED").lower() in ("true", "1", "yes")

        if env_overrides:
            # Redact sensitive keys for logging
            redacted_overrides = {
                k: v for k, v in env_overrides.items()
                if 'password' not in k.lower() and 'token' not in k.lower()
            }
            for k in env_overrides:
                if 'password' in k.lower() or 'token' in k.lower():
                    redacted_overrides[k] = '********'

            logger.debug(
                f"Applying environment variable overrides: {redacted_overrides}")
            config.update(env_overrides)

        # Default availability topic if not set
        if not config.get("mqtt_availability_topic"):
            config["mqtt_availability_topic"] = f"{config['mqtt_topic']}/status"
            logger.debug(
                f"Defaulting mqtt_availability_topic to: {config['mqtt_availability_topic']}")

        # Parse sensors from config file (already loaded in config dict)
        # Convert dicts to SensorConfig objects
        sensors_data = config.get("sensors", [])
        sensors = []
        for s in sensors_data:
            if isinstance(s, dict):
                sensors.append(SensorConfig(**s))
        config["sensors"] = sensors

        # Validate configuration
        cls._validate_config(config)

        logger.info(
            f"Configuration loaded: {config['http_url']} -> {config['mqtt_topic']}")
        logger.info(
            f"SSL verification: {'enabled' if config['verify_ssl'] else 'disabled'}")
        if config['dry_run']:
            logger.warning(
                "DRY RUN MODE: MQTT publishing disabled (logging only)")
        if sensors:
            logger.info(f"Configured {len(sensors)} Home Assistant sensors")

        return cls(**config)

    @staticmethod
    def _validate_config(config: dict) -> None:
        """Validate configuration values for security and correctness."""
        # Validate HTTP URL
        http_url = config.get("http_url", "")
        if not http_url:
            raise ValueError("http_url is required")
        if not http_url.startswith(("http://", "https://")):
            raise ValueError(
                f"http_url must start with http:// or https://, got: {http_url}")

        # Validate system_id
        system_id = config.get("system_id", "")
        if not system_id:
            raise ValueError("system_id is required")

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

