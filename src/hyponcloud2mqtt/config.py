"""Configuration loading module."""

import os
import yaml


def load_config():
    """Loads configuration from config.yaml and allows overriding with environment variables."""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    # Override with environment variables
    for category, settings in get_default_config().items():
        if category not in config:
            config[category] = {}
        for key, value in settings.items():
            env_var_name = f"{category.upper()}_{key.upper()}"
            env_var_value = os.getenv(env_var_name)
            if env_var_value is not None:
                # Try to convert to the same type as the value in the YAML file
                try:
                    if isinstance(value, bool):
                        config[category][key] = env_var_value.lower() in ("true", "1", "t")
                    elif isinstance(value, int):
                        config[category][key] = int(env_var_value)
                    elif isinstance(value, list):
                        config[category][key] = [item.strip() for item in env_var_value.split(',')]
                    else:
                        config[category][key] = env_var_value
                except (ValueError, TypeError):
                    # If conversion fails, use the raw string value
                    config[category][key] = env_var_value
            elif key not in config[category]:
                config[category][key] = value


    return config

def get_default_config():
    """Returns the default configuration structure and values."""
    return {
        "hypon": {
            "user": "YOUR_USER",
            "password": "YOUR_PASSWORD",
            "api_base_url": "https://api.hypon.cloud/v2",
            "system_ids": ["YOUR_SYSTEM_ID"],
            "interval": 60,
            "retries": 0,
        },
        "mqtt": {
            "host": "localhost",
            "port": 1883,
            "user": "",
            "password": "",
            "topic": "hyponcloud2mqtt",
            "retain": False,
            "ssl": False,
        },
    }


config = load_config()