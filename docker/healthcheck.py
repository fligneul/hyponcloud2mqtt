#!/usr/bin/env python3
"""
Simple health check script for hyponcloud2mqtt daemon.
Checks if the main process is running and responsive by querying the internal HTTP server.
"""
import sys
import urllib.request
import urllib.error


def main():
    try:
        # Query the internal health endpoint
        with urllib.request.urlopen("http://localhost:8080/health", timeout=2) as response:
            if response.status == 200:
                sys.exit(0)
            else:
                print(f"Health check failed with status: {response.status}", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"Health check failed: HTTP {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
