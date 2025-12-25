import http.server
import socketserver
import logging

logger = logging.getLogger(__name__)


class HealthContext:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client


class HealthHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            is_healthy = self.server.context.mqtt_client.connected or self.server.context.mqtt_client.dry_run

            if is_healthy:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "healthy"}')
            else:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    b'{"status": "unhealthy", "reason": "mqtt_disconnected"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default logging
        pass


class HealthServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, context):
        self.context = context
        super().__init__(server_address, RequestHandlerClass)
