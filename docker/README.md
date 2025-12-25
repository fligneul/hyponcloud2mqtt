# hyponcloud2mqtt

A bridge to connect the Hypon Cloud API to an MQTT broker. This application periodically fetches data from your Hypon system and publishes it to your MQTT broker, allowing for easy integration with home automation systems like Home Assistant.

> [!NOTE]
> This project was developed and tested using data from an **HMS800-C** inverter.

## Quick Start

### Docker Run

```bash
docker run -d \
  --name hyponcloud2mqtt \
  --restart unless-stopped \
  -e HTTP_URL="http://192.168.1.100" \
  -e SYSTEM_IDS="12345,67890" \
  -e API_USERNAME="your_username" \
  -e API_PASSWORD="your_password" \
  -e MQTT_BROKER="192.168.1.10" \
  -e MQTT_TOPIC="solar/inverter" \
  fligneul/hyponcloud2mqtt:latest
```

### Docker Compose

```yaml
services:
  hyponcloud2mqtt:
    image: fligneul/hyponcloud2mqtt:latest
    container_name: hyponcloud2mqtt
    restart: unless-stopped
    environment:
      HTTP_URL: "http://192.168.1.100"
      SYSTEM_IDS: "your_system_id_1"
      API_USERNAME: "your_username"
      API_PASSWORD: "your_password"
      MQTT_BROKER: "mosquitto"
      MQTT_TOPIC: "solar/inverter"
```

## Configuration

### Environment Variables

> [!NOTE]
> Variables marked as **Config*** are required **only if** they are not provided in the `config.yaml` file. If no configuration file is used, these environment variables must be set.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HTTP_URL` | Config* | - | Base URL of the API (e.g., `http://192.168.1.100`) |
| `SYSTEM_IDS` | Config* | - | Comma-separated list of system IDs to monitor |
| `API_USERNAME` | Config* | - | API username for authentication |
| `API_PASSWORD` | Config* | - | API password for authentication |
| `HTTP_INTERVAL` | No | `60` | Fetch interval in seconds |
| `MQTT_BROKER` | No | `localhost` | MQTT broker address |
| `MQTT_PORT` | No | `1883` | MQTT broker port |
| `MQTT_TOPIC` | No | `home/data` | MQTT topic to publish to |
| `MQTT_USERNAME` | No | - | MQTT username (optional) |
| `MQTT_PASSWORD` | No | - | MQTT password (optional) |
| `MQTT_CLIENT_ID` | No | `hyponcloud2mqtt` | MQTT client ID (optional) |
| `MQTT_AVAILABILITY_TOPIC` | No | `{MQTT_TOPIC}/status` | MQTT availability topic |
| `HA_DISCOVERY_ENABLED` | No | `true` | Enable Home Assistant discovery |
| `HA_DISCOVERY_PREFIX` | No | `homeassistant` | Home Assistant discovery prefix |
| `DEVICE_NAME` | No | `hyponcloud2mqtt` | Device name for Home Assistant |
| `VERIFY_SSL` | No | `true` | Verify SSL certificates (set to `false` for self-signed certs) |
| `DRY_RUN` | No | `false` | If `true`, log MQTT messages instead of publishing |
| `CONFIG_FILE` | No | `config.yaml` | Path to config file |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MQTT_TLS_ENABLED` | No | `false` | Enable MQTT TLS |
| `MQTT_TLS_INSECURE` | No | `false` | Disable TLS certificate verification |
| `MQTT_CA_PATH` | No | - | Path to custom CA certificate for MQTT |

## License

This project is licensed under the GNU Affero General Public License v3.0.
