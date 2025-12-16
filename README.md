# hyponcloud2mqtt

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/hyponcloud2mqtt.svg)](https://badge.fury.io/py/hyponcloud2mqtt)
[![Tests](https://github.com/fligneul/hyponcloud2mqtt/workflows/Test/badge.svg)](https://github.com/fligneul/hyponcloud2mqtt/actions)

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
  username/hyponcloud2mqtt:latest
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

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HTTP_URL` | Yes | - | Base URL of the API (e.g., `http://192.168.1.100`) |
| `SYSTEM_IDS` | Yes | - | Comma-separated list of system IDs to monitor |
| `API_USERNAME` | Yes | - | API username for authentication |
| `API_PASSWORD` | Yes | - | API password for authentication |
| `HTTP_INTERVAL` | No | `60` | Fetch interval in seconds |
| `MQTT_BROKER` | No | `localhost` | MQTT broker address |
| `MQTT_PORT` | No | `1883` | MQTT broker port |
| `MQTT_TOPIC` | No | `home/data` | MQTT topic to publish to |
| `MQTT_USERNAME` | No | - | MQTT username (optional) |
| `MQTT_PASSWORD` | No | - | MQTT password (optional) |
| `MQTT_AVAILABILITY_TOPIC` | No | `{MQTT_TOPIC}/status` | MQTT availability topic |
| `HA_DISCOVERY_ENABLED` | No | `true` | Enable Home Assistant discovery |
| `HA_DISCOVERY_PREFIX` | No | `homeassistant` | Home Assistant discovery prefix |
| `DEVICE_NAME` | No | `hyponcloud2mqtt` | Device name for Home Assistant |
| `VERIFY_SSL` | No | `true` | Verify SSL certificates (set to `false` for self-signed certs) |
| `DRY_RUN` | No | `false` | If `true`, log MQTT messages instead of publishing |
| `CONFIG_FILE` | No | `config.yaml` | Path to config file |

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
version: '3.8'
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
version: '3.8'
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

The daemon publishes a merged JSON containing data from multiple endpoints. Example payload for HMS800-C inverter:

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
  "gateway": {
    "online": 1,
    "offline": 0
  },
  "inverter": {
    "online": 1,
    "normal": 1,
    "offline": 0,
    "fault": 0,
    "wait": 0
  }
}
```

## Development

### Setup

### Setup

> [!NOTE]
> This project requires **Python 3.11** or higher.


```bash
# Clone repository
git clone https://github.com/USERNAME/hyponcloud2mqtt.git
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
# Run all tests
pytest

# Run with coverage
pytest --cov=hyponcloud2mqtt

# Run specific test file
pytest tests/test_integration.py
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

## Architecture

The daemon operates in a simple loop:

1. **Login**: Authenticates with the API and retrieves a Bearer token
2. **Fetch**: Calls 3 hardcoded endpoints (`/monitor?refresh=true`, `/production2`, `/status`)
3. **Validate**: Checks for `code: 20000` (success) or `code: 50008` (auth failed)
4. **Merge**: Combines selected fields from all 3 responses into a single JSON
5. **Publish**: Sends merged data to MQTT topic
6. **Re-auth**: Automatically re-authenticates if token expires (code 50008)
7. **Sleep**: Waits for configured interval, then repeats

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

## CI/CD

The project includes GitHub Actions workflows for:

- **Testing**: Runs on every push/PR
- **Release Please**: Automatically creates release PRs with changelog
- **Publishing**: Publishes to PyPI and Docker Hub on release

### Release Process

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [release-please](https://github.com/googleapis/release-please) for automated releases:

1. **Commit with conventional format**:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug"
   ```

2. **Push to main** - release-please automatically:
   - Creates/updates a release PR
   - Generates CHANGELOG.md
   - Bumps version based on commits

3. **Merge release PR** - triggers:
   - GitHub release creation
   - PyPI publishing
   - Docker Hub multi-arch build

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit message guidelines.

### Required Secrets

For publishing, configure these GitHub secrets:
- `PYPI_TOKEN`: PyPI API token
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Conventional commit guidelines
- Pull request process
- Code style guidelines

## Support

- **Issues**: [GitHub Issues](https://github.com/fligneul/hyponcloud2mqtt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fligneul/hyponcloud2mqtt/discussions)
