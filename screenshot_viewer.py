#!/usr/bin/env python3
"""
Interface Web pour visualiser les screenshots du scanner RDV
"""
import os
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import threading
import json
from datetime import datetime

class ScreenshotViewerHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Gérer les requêtes GET"""
        path = unquote(self.path)
        
        if path == '/':
            self.serve_index()
        elif path == '/api/screenshots':
            self.serve_screenshots_list()
        elif path.startswith('/screenshots/'):
            self.serve_file(path)
        elif path == '/health':
            self.serve_health()
        else:
            self.send_error(404)
    
    def serve_index(self):
        """Page d'accueil avec liste des screenshots"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎯 RDV Scanner - Screenshots</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .file-list { display: grid; gap: 10px; }
                .file-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                .file-name { font-weight: bold; }
                .file-info { color: #666; font-size: 0.9em; }
                .btn { background: #2563eb; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
                .btn:hover { background: #1d4ed8; }
                .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
                .info { background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 RDV Scanner - Monitoring Screenshots</h1>
                <p>Interface de visualisation des captures d'écran du scanner</p>
            </div>
            
            <div class="container">
                <div class="status info">
                    📊 <strong>Service Status:</strong> Actif | 
                    🕒 <strong>Dernière mise à jour:</strong> <span id="timestamp"></span>
                </div>
                
                <h2>📸 Screenshots Disponibles</h2>
                <div id="files-container">
                    <p>Chargement...</p>
                </div>
                
                <button onclick="refreshFiles()" class="btn">🔄 Actualiser</button>
            </div>

            <script>
                function formatFileSize(bytes) {
                    if (bytes === 0) return '0 B';
                    const k = 1024;
                    const sizes = ['B', 'KB', 'MB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                }
                
                function formatDate(dateStr) {
                    return new Date(dateStr).toLocaleString('fr-FR');
                }
                
                function loadFiles() {
                    fetch('/api/screenshots')
                        .then(response => response.json())
                        .then(data => {
                            const container = document.getElementById('files-container');
                            if (data.files.length === 0) {
                                container.innerHTML = '<p>Aucun screenshot disponible pour le moment.</p>';
                                return;
                            }
                            
                            let html = '<div class="file-list">';
                            data.files.forEach(file => {
                                const isImage = file.name.endsWith('.png') || file.name.endsWith('.jpg');
                                const isAudio = file.name.endsWith('.wav') || file.name.endsWith('.mp3');
                                const icon = isImage ? '🖼️' : (isAudio ? '🎵' : '📄');
                                
                                html += `
                                    <div class="file-item">
                                        <div>
                                            <span class="file-name">${icon} ${file.name}</span>
                                            <div class="file-info">
                                                Taille: ${formatFileSize(file.size)} | 
                                                Modifié: ${formatDate(file.modified)}
                                            </div>
                                        </div>
                                        <div>
                                            <a href="/screenshots/${file.name}" class="btn" target="_blank">
                                                ${isImage ? '👁️ Voir' : '⬇️ Télécharger'}
                                            </a>
                                        </div>
                                    </div>
                                `;
                            });
                            html += '</div>';
                            container.innerHTML = html;
                        })
                        .catch(error => {
                            document.getElementById('files-container').innerHTML = 
                                '<p style="color: red;">Erreur lors du chargement des fichiers.</p>';
                        });
                }
                
                function refreshFiles() {
                    loadFiles();
                    document.getElementById('timestamp').textContent = new Date().toLocaleString('fr-FR');
                }
                
                // Charger au démarrage
                document.addEventListener('DOMContentLoaded', function() {
                    refreshFiles();
                    // Auto-refresh toutes les 30 secondes
                    setInterval(refreshFiles, 30000);
                });
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_screenshots_list(self):
        """API pour lister les screenshots"""
        try:
            screenshots_dir = '/app/screenshots'
            files = []
            
            if os.path.exists(screenshots_dir):
                for filename in os.listdir(screenshots_dir):
                    filepath = os.path.join(screenshots_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        files.append({
                            'name': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            
            # Trier par date de modification (plus récent en premier)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            response = {
                'files': files,
                'total': len(files),
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_file(self, path):
        """Servir un fichier screenshot"""
        try:
            # Nettoyer le chemin
            filename = path.replace('/screenshots/', '')
            filepath = os.path.join('/app/screenshots', filename)
            
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                self.send_error(404, "Fichier non trouvé")
                return
            
            # Déterminer le type MIME
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Lire et servir le fichier
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            
            # Headers pour le téléchargement si ce n'est pas une image
            if not mime_type.startswith('image/'):
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_health(self):
        """Endpoint de santé"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'screenshot_viewer',
            'version': '1.0.0'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(health_status).encode())
    
    def log_message(self, format, *args):
        """Logs silencieux"""
        pass

def start_screenshot_viewer(port=8081):
    """Démarre le serveur de visualisation des screenshots"""
    try:
        server = HTTPServer(('0.0.0.0', port), ScreenshotViewerHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print(f"🖼️ Screenshot viewer démarré sur ::{port}")
        return server
    except Exception as e:
        print(f"Erreur démarrage screenshot viewer: {e}")
        return None

if __name__ == "__main__":
    server = start_screenshot_viewer(8081)
    if server:
        print("Screenshot viewer en cours d'exécution...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Arrêt du serveur...")
            server.shutdown()