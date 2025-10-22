# Health check endpoint (optionnel pour certains hébergeurs)
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from datetime import datetime

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'rdv_scanner',
                'version': '1.0.0'
            }
            
            self.wfile.write(json.dumps(health_status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Désactiver les logs HTTP pour éviter le spam
        pass

def start_health_server():
    """Démarre le serveur de health check en arrière-plan"""
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("🏥 Health check server démarré sur :8080/health")

if __name__ == "__main__":
    start_health_server()
    import time
    time.sleep(60)  # Test de 60 secondes