# hyponcloud2mqtt

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![PyPI version](https://badge.fury.io/py/hyponcloud2mqtt.svg)](https://badge.fury.io/py/hyponcloud2mqtt)
[![Docker Image Version](https://img.shields.io/docker/v/fligneul/hyponcloud2mqtt?sort=semver&label=docker)](https://hub.docker.com/r/fligneul/hyponcloud2mqtt)
[![Tests](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/test.yml/badge.svg)](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/test.yml)

A bridge to connect the Hypon Cloud API to an MQTT broker. This application periodically fetches data from your Hypon system and publishes it to your MQTT broker, allowing for easy integration with home automation systems like Home Assistant.

> [!NOTE]
> This project was developed and tested using data from an **HMS800-C** inverter. If you are using a different Hypon inverter model and find that some data points are missing or incorrectly mapped, please open an issue on the GitHub repository.

## Features

- Fetches the latest data from the Hypon Cloud API.
- Publishes data to a configurable MQTT topic.
- Publishes service status (online/offline) using MQTT Last Will and Testament (LWT).
- Automatically handles API token acquisition and renewal.
- Configuration via a simple config.yaml file.
- Support for environment variables for Dockerized deployments.
- Can be run directly with Python or as a Docker container.
- Installable via PyPI.

## Prerequisites

- Python 3.11 or later
- A Hypon Cloud account
- An MQTT broker
- Docker (optional, for containerized deployment)

## Quick Start

### Docker (Recommended)

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

```bash
# Copy example and customize
cp docker-compose.yml.example docker-compose.yml
# Edit docker-compose.yml with your settings
docker-compose up -d
```

### Python (PyPI)

```bash
pip install hyponcloud2mqtt

# Create config file
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Run
hyponcloud2mqtt
```

## Configuration

Configuration can be provided via **environment variables** or a **YAML config file**. Environment variables take precedence over config file values.

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

### Configuration File

See [`config.yaml.example`](config.yaml.example) for a complete example with Home Assistant sensor definitions.

```yaml
http_url: "http://192.168.1.100"
api_username: "your_username"
api_password: "your_password"
http_interval: 60

mqtt_broker: "localhost"
mqtt_port: 1883
mqtt_topic: "solar/inverter"

ha_discovery_prefix: "homeassistant"
device_name: "Solar Inverter"
```

## Secrets Management

### Option 1: Environment File (Recommended for Docker Compose)

Use a `.env` file that is **not committed to version control**:

**Step 1: Create `.env` file**
```bash
# Create .env file with your secrets
cat > .env << 'EOF'
HTTP_URL=http://192.168.1.100
API_USERNAME=your_username
API_PASSWORD=your_password
MQTT_BROKER=192.168.1.10
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_pass
EOF

# Secure the file (Linux/Mac)
chmod 600 .env

# Add to .gitignore
echo ".env" >> .gitignore
```

**Step 2: Update `docker-compose.yml`**
```yaml
services:
  hyponcloud2mqtt:
    image: fligneul/hyponcloud2mqtt:latest
    env_file:
      - .env  # Loads all variables from .env file
    restart: unless-stopped
```

**Step 3: Deploy**
```bash
docker-compose up -d
```

**Pros**: Simple, works with Docker Compose, secrets not in compose file
**Cons**: Secrets visible in container environment

### Option 2: Mounted Configuration File (More Secure)

Mount a configuration file as read-only volume:

**Step 1: Create secrets directory**
```bash
# Create directory for secrets
mkdir -p secrets
chmod 700 secrets

# Create config file
cat > secrets/config.yaml << 'EOF'
http_url: "http://192.168.1.100"
api_username: "your_username"
api_password: "your_password"
mqtt_broker: "192.168.1.10"
mqtt_username: "mqtt_user"
mqtt_password: "mqtt_pass"
EOF

# Secure the file
chmod 600 secrets/config.yaml

# Add to .gitignore
echo "secrets/" >> .gitignore
```

**Step 2: Update `docker-compose.yml`**
```yaml
services:
  hyponcloud2mqtt:
    image: fligneul/hyponcloud2mqtt:latest
    volumes:
      - ./secrets/config.yaml:/app/config.yaml:ro  # Read-only mount
    environment:
      CONFIG_FILE: /app/config.yaml
    restart: unless-stopped
```

**Step 3: Deploy**
```bash
docker-compose up -d
```

**Pros**: Secrets not in environment variables, file permissions control access
**Cons**: Secrets still plaintext on disk (use disk encryption for additional security)

### Security Best Practices

1. **Never commit secrets to git**
   ```bash
   # Add to .gitignore
   .env
   secrets/
   config.yaml
   *.secret
   ```

2. **Use restrictive file permissions**
   ```bash
   chmod 600 .env secrets/config.yaml  # Owner read/write only
   chmod 700 secrets/                   # Owner access only
   ```

3. **Rotate credentials regularly**
   - Change API passwords periodically
   - Update MQTT credentials
   - Restart container after rotation

4. **Use separate credentials per environment**
   - Different secrets for dev/staging/production
   - Never reuse production credentials

## Home Assistant Integration

The daemon automatically publishes MQTT Discovery messages for configured sensors. Home Assistant will auto-detect and create entities.

### Published MQTT Data

| Field | Description | Unit | Decimal Precision |
|-------|-------------|------|-------------------|
| `percent` | Capacity Factor | % | 2 |
| `w_cha` | Charging Power | W | 0 |
| `power_pv` | PV Power | W | 0 |
| `today_generation` | Today Energy | kWh | 2 |
| `month_generation` | Month Energy | kWh | 2 |
| `year_generation` | Year Energy | kWh | 2 |
| `total_generation` | Total Energy | kWh | 2 |
| `co2` | CO2 Saved | kg | 2 |
| `tree` | Trees Planted | - | 2 |
| `diesel` | Diesel Saved | L | 2 |
| `today_revenue` | Today Revenue | - | 2 |
| `month_revenue` | Month Revenue | - | 2 |
| `total_revenue` | Total Revenue | - | 2 |
| `gateway_online` | Gateway Online | - | 0 |
| `gateway_offline` | Gateway Offline | - | 0 |
| `inverter_online` | Inverter Online | - | 0 |
| `inverter_normal` | Inverter Normal | - | 0 |
| `inverter_offline` | Inverter Offline | - | 0 |
| `inverter_fault` | Inverter Fault | - | 0 |
| `inverter_wait` | Inverter Wait | - | 0 |

### Example Payload

Example payload for HMS800-C inverter:

```json
{
  "percent": 5.39,
  "meter_power": 0,
  "power_load": 41,
  "w_cha": 0,
  "power_pv": 41,
  "today_generation": 0.02,
  "month_generation": 0.09,
  "year_generation": 94.42,
  "total_generation": 94.42,
  "co2": 2.83,
  "tree": 0.16,
  "diesel": 10.49,
  "today_revenue": 0,
  "month_revenue": 0.02,
  "total_revenue": 16.16,
  "gateway_online": 1,
  "gateway_offline": 0,
  "inverter_online": 1,
  "inverter_normal": 1,
  "inverter_offline": 0,
  "inverter_fault": 0,
  "inverter_wait": 0
}
```

## Development

### Setup

> [!NOTE]
> This project requires **Python 3.11** or higher.


```bash
# Clone repository
git clone https://github.com/fligneul/hyponcloud2mqtt.git
cd hyponcloud2mqtt

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip (required for editable installs with pyproject.toml)
pip install --upgrade pip

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# Run unit tests
pytest

# Run tests with coverage
pytest --cov=hyponcloud2mqtt
```

### Integration Tests

The integration tests verify the daemon's behavior with a real MQTT broker and a mocked API (WireMock).

#### Automated (Cross-Platform)

The easiest way to run integration tests is using the provided Python script:

```bash
# Mac / Linux
python3 scripts/run_integration_tests.py

# Windows
python scripts\run_integration_tests.py
```

This script will automatically start the required Docker containers, set the environment variables, and run the tests.

#### Manual

If you prefer to run the steps manually:

1. **Start dependencies**:
   ```bash
   docker compose -f docker-compose.dev.yml up mosquitto wiremock -d
   ```

2. **Run the test with environment variables**:

   **Mac / Linux:**
   ```bash
   export HTTP_URL=http://localhost:8080
   export SYSTEM_IDS=your_system_id_1
   export API_USERNAME=test_user
   export API_PASSWORD=test_password
   export MQTT_BROKER=localhost
   .venv/bin/python -m pytest tests/test_wiremock_integration.py
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:HTTP_URL="http://localhost:8080"
   $env:SYSTEM_IDS="your_system_id_1"
   $env:API_USERNAME="test_user"
   $env:API_PASSWORD="test_password"
   $env:MQTT_BROKER="localhost"
   .\.venv\Scripts\python -m pytest tests/test_wiremock_integration.py
   ```

### Local Development with WireMock

You can run the application locally without external dependencies using WireMock to simulate the API and a local MQTT broker.

**Using Docker Compose (Recommended):**

```bash
# Starts the application, WireMock, and Mosquitto
docker-compose -f docker-compose.dev.yml up
```

The environment will be pre-configured with:
- **WireMock** on port 8080 (simulating the API)
- **Mosquitto** on port 1883 (MQTT broker)
- **Application** configured to talk to both

## Troubleshooting

### Authentication Failures

If you see `code: 50008` errors:
- Verify `API_USERNAME` and `API_PASSWORD` are correct
- Check API logs for authentication issues
- The daemon will automatically retry login

### MQTT Connection Issues

- Verify `MQTT_BROKER` is reachable
- Check `MQTT_USERNAME` and `MQTT_PASSWORD` if required
- Ensure MQTT broker allows connections from daemon's IP

### No Data in Home Assistant

- Check MQTT topic in Home Assistant MQTT integration
- Verify `HA_DISCOVERY_ENABLED` is not set to `false` (default: `true`)
- Verify `HA_DISCOVERY_PREFIX` matches Home Assistant config (default: `homeassistant`)
- Check Home Assistant logs for discovery messages

### SSL Certificate Errors

If you see SSL certificate verification errors:
- **For production**: Ensure your API server has a valid SSL certificate
- **For self-signed certificates**: Set `VERIFY_SSL=false` in environment or `verify_ssl: false` in config.yaml
- **Security note**: Only disable SSL verification if you trust the network and understand the security implications

### Docker Health Check Failing

The daemon includes a basic health check. If failing:
- Check container logs: `docker logs hyponcloud2mqtt`
- Verify API is reachable from container
- Ensure MQTT broker is accessible

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Conventional commit guidelines
- Pull request process
- Code style guidelines

## Support

- **Issues**: [GitHub Issues](https://github.com/fligneul/hyponcloud2mqtt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fligneul/hyponcloud2mqtt/discussions)
