#!/usr/bin/env python3
"""
Interface Web sécurisée pour visualiser les screenshots du scanner RDV
"""
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes
import threading
import base64
import hashlib
import secrets

class AuthMixin:
    """Mixin pour l'authentification des endpoints"""
    
    def check_auth(self):
        """Vérifie l'authentification via token ou basic auth"""
        # 1. Token dans query params ou header
        if self.check_token_auth():
            return True
            
        # 2. Basic Auth si configuré
        if self.check_basic_auth():
            return True
            
        return False
    
    def check_token_auth(self):
        """Vérifie l'authentification par token"""
        expected_token = os.getenv('SCREENSHOT_TOKEN')
        if not expected_token:
            return False
            
        # Token dans l'URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        token_from_url = query_params.get('token', [None])[0]
        
        # Token dans le header
        token_from_header = self.headers.get('X-Screenshot-Token')
        
        return (token_from_url == expected_token or 
                token_from_header == expected_token)
    
    def check_basic_auth(self):
        """Vérifie l'authentification basique"""
        username = os.getenv('SCREENSHOT_USERNAME')
        password = os.getenv('SCREENSHOT_PASSWORD')
        
        if not username or not password:
            return False
            
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return False
            
        try:
            encoded_credentials = auth_header[6:]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            provided_username, provided_password = decoded_credentials.split(':', 1)
            return provided_username == username and provided_password == password
        except:
            return False
    
    def send_auth_required(self):
        """Envoie une réponse 401 avec demande d'authentification"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Screenshot Viewer"')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'error': 'Authentification requise',
            'message': 'Token manquant ou invalide',
            'help': {
                'token_url': '?token=YOUR_TOKEN',
                'token_header': 'X-Screenshot-Token: YOUR_TOKEN',
                'basic_auth': 'Authorization: Basic base64(username:password)'
            }
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

class ScreenshotViewerHandler(AuthMixin, BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Gère les requêtes GET"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Health check public (pour Railway)
            if path == '/health':
                self.serve_health()
                return
            
            # Vérification de l'authentification pour les autres endpoints
            if not self.check_auth():
                self.send_auth_required()
                return
            
            if path == '/' or path == '/index.html':
                self.serve_index()
            elif path == '/api/screenshots':
                self.serve_api_screenshots()
            elif path == '/api/cleanup':
                self.serve_cleanup()
            elif path.startswith('/screenshots/'):
                self.serve_screenshot_file(path)
            else:
                self.send_error(404, 'Page non trouvée')
        except Exception as e:
            self.send_error(500, f'Erreur serveur: {str(e)}')
    
    def serve_index(self):
        """Page d'accueil avec liste des screenshots"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎯 RDV Scanner - Screenshots</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: #f5f5f5; 
                    line-height: 1.6;
                }
                .header { 
                    background: #2c3e50; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin-bottom: 20px;
                    text-align: center;
                }
                .auth-info {
                    background: #e8f5e8; 
                    padding: 10px; 
                    margin-bottom: 20px; 
                    border-radius: 5px; 
                    text-align: center;
                    border-left: 4px solid #27ae60;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .toolbar {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 6px;
                    border: 1px solid #e9ecef;
                }
                .cleanup-section {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .cleanup-btn {
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: background 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .cleanup-btn:hover {
                    background: #c82333;
                }
                .cleanup-btn:disabled {
                    background: #6c757d;
                    cursor: not-allowed;
                }
                .cleanup-status {
                    font-size: 0.9em;
                    color: #666;
                }
                .stats-info {
                    font-size: 0.9em;
                    color: #495057;
                }
                .file-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
                    gap: 20px; 
                    margin-top: 20px;
                }
                .file-item { 
                    border: 1px solid #ddd; 
                    border-radius: 8px; 
                    padding: 15px; 
                    background: #fafafa;
                    transition: transform 0.2s;
                }
                .file-item:hover { 
                    transform: translateY(-2px); 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                .file-name { 
                    font-weight: bold; 
                    color: #2c3e50; 
                    margin-bottom: 10px;
                    word-break: break-all;
                }
                .file-info { 
                    color: #666; 
                    font-size: 0.9em; 
                    margin-bottom: 10px;
                }
                .file-actions {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                .btn { 
                    padding: 8px 16px; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                    text-decoration: none;
                    display: inline-block;
                    font-size: 0.9em;
                    transition: background 0.2s;
                }
                .btn-primary { 
                    background: #3498db; 
                    color: white; 
                }
                .btn-primary:hover { 
                    background: #2980b9; 
                }
                .btn-success { 
                    background: #27ae60; 
                    color: white; 
                }
                .btn-success:hover { 
                    background: #219a52; 
                }
                .preview { 
                    max-width: 100%; 
                    max-height: 200px; 
                    border-radius: 4px; 
                    margin: 10px 0;
                    border: 1px solid #ddd;
                }
                .status { 
                    text-align: center; 
                    padding: 20px; 
                    color: #666;
                }
                .loading { 
                    text-align: center; 
                    padding: 40px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    color: #666;
                    border-top: 1px solid #eee;
                }
                @media (max-width: 768px) {
                    body { margin: 10px; }
                    .file-grid { grid-template-columns: 1fr; }
                    .file-actions { flex-direction: column; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 RDV Scanner - Screenshots</h1>
                <p>Interface de visualisation des captures d'écran</p>
            </div>
            
            <div class="auth-info">
                🔒 <strong>Session authentifiée</strong> - Accès autorisé aux screenshots
            </div>
            
            <div class="container">
                <div class="toolbar">
                    <div class="stats-info">
                        <span id="fileCount">Chargement...</span>
                    </div>
                    <div class="cleanup-section">
                        <div class="cleanup-status" id="cleanupStatus"></div>
                        <button class="cleanup-btn" id="cleanupBtn" onclick="cleanupScreenshots()">
                            🗑️ Nettoyer les Screenshots
                        </button>
                    </div>
                </div>
                
                <div class="loading">
                    🔄 Chargement des screenshots...
                </div>
                
                <div id="filesList"></div>
                
                <div class="footer">
                    <p>🔄 Auto-refresh toutes les 30 secondes</p>
                    <p>📊 Scanner RDV avec résolution multimodale des captcha</p>
                </div>
            </div>

            <script>
                async function loadScreenshots() {
                    try {
                        const urlParams = new URLSearchParams(window.location.search);
                        const token = urlParams.get('token');
                        const url = token ? `/api/screenshots?token=${token}` : '/api/screenshots';
                        
                        const response = await fetch(url);
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        
                        const data = await response.json();
                        displayFiles(data.files);
                        
                        document.querySelector('.loading').style.display = 'none';
                        
                    } catch (error) {
                        document.querySelector('.loading').innerHTML = 
                            `❌ Erreur de chargement: ${error.message}`;
                    }
                }

                function displayFiles(files) {
                    const container = document.getElementById('filesList');
                    const fileCountElement = document.getElementById('fileCount');
                    
                    // Mettre à jour les statistiques
                    if (files && files.length > 0) {
                        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
                        fileCountElement.textContent = `📊 ${files.length} fichiers • ${formatSize(totalSize)}`;
                    } else {
                        fileCountElement.textContent = '📊 0 fichiers • 0 B';
                    }
                    
                    if (!files || files.length === 0) {
                        container.innerHTML = '<div class="status">📭 Aucun screenshot disponible</div>';
                        return;
                    }

                    const urlParams = new URLSearchParams(window.location.search);
                    const token = urlParams.get('token');
                    const tokenParam = token ? `?token=${token}` : '';

                    container.innerHTML = `
                        <h2>📸 Screenshots (${files.length})</h2>
                        <div class="file-grid">
                            ${files.map(file => `
                                <div class="file-item">
                                    <div class="file-name">📄 ${file.name}</div>
                                    <div class="file-info">
                                        📏 ${formatSize(file.size)} | 
                                        🕒 ${formatDate(file.modified)}
                                    </div>
                                    ${file.name.endsWith('.png') ? 
                                        `<img src="/screenshots/${file.name}${tokenParam}" 
                                              class="preview" 
                                              alt="Preview" 
                                              loading="lazy">` : ''}
                                    <div class="file-actions">
                                        <a href="/screenshots/${file.name}${tokenParam}" 
                                           class="btn btn-primary" 
                                           target="_blank">
                                           👁️ Voir
                                        </a>
                                        <a href="/screenshots/${file.name}${tokenParam}" 
                                           class="btn btn-success" 
                                           download="${file.name}">
                                           ⬇️ Télécharger
                                        </a>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                async function cleanupScreenshots() {
                    const button = document.getElementById('cleanupBtn');
                    const status = document.getElementById('cleanupStatus');
                    
                    if (!confirm('⚠️ Êtes-vous sûr de vouloir supprimer TOUS les screenshots ?\\n\\nCette action est irréversible !')) {
                        return;
                    }
                    
                    try {
                        button.disabled = true;
                        button.innerHTML = '⏳ Nettoyage...';
                        status.textContent = 'Suppression en cours...';
                        
                        const urlParams = new URLSearchParams(window.location.search);
                        const token = urlParams.get('token');
                        const url = token ? `/api/cleanup?token=${token}` : '/api/cleanup';
                        
                        const response = await fetch(url);
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            status.textContent = `✅ ${result.deleted_count} fichier(s) supprimé(s)`;
                            status.style.color = '#28a745';
                            
                            // Recharger la liste après 1 seconde
                            setTimeout(() => {
                                loadScreenshots();
                                status.textContent = '';
                                status.style.color = '#666';
                            }, 2000);
                        } else {
                            throw new Error(result.error || 'Erreur inconnue');
                        }
                        
                    } catch (error) {
                        status.textContent = `❌ Erreur: ${error.message}`;
                        status.style.color = '#dc3545';
                        
                        setTimeout(() => {
                            status.textContent = '';
                            status.style.color = '#666';
                        }, 5000);
                        
                    } finally {
                        button.disabled = false;
                        button.innerHTML = '🗑️ Nettoyer les Screenshots';
                    }
                }

                function formatSize(bytes) {
                    if (bytes === 0) return '0 B';
                    const k = 1024;
                    const sizes = ['B', 'KB', 'MB', 'GB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
                }

                function formatDate(dateString) {
                    const date = new Date(dateString);
                    return date.toLocaleString('fr-FR');
                }

                // Chargement initial
                loadScreenshots();
                
                // Auto-refresh toutes les 30 secondes
                setInterval(loadScreenshots, 30000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_api_screenshots(self):
        """API REST pour lister les screenshots"""
        screenshots_dir = "/app/screenshots"
        if not os.path.exists(screenshots_dir):
            screenshots_dir = "./screenshots"
        
        files = []
        try:
            if os.path.exists(screenshots_dir):
                for filename in os.listdir(screenshots_dir):
                    if filename.endswith(('.png', '.wav')):
                        filepath = os.path.join(screenshots_dir, filename)
                        stat = os.stat(filepath)
                        files.append({
                            'name': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                
                # Trier par date de modification (plus récent en premier)
                files.sort(key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            files = []
        
        response = {
            'files': files,
            'total': len(files),
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def serve_screenshot_file(self, path):
        """Sert un fichier screenshot spécifique"""
        filename = path.split('/')[-1]
        
        # Vérification de sécurité
        if '..' in filename or '/' in filename:
            self.send_error(403, 'Accès interdit')
            return
        
        screenshots_dir = "/app/screenshots"
        if not os.path.exists(screenshots_dir):
            screenshots_dir = "./screenshots"
        
        filepath = os.path.join(screenshots_dir, filename)
        
        if not os.path.exists(filepath):
            self.send_error(404, 'Fichier non trouvé')
            return
        
        # Déterminer le type MIME
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f'Erreur de lecture: {str(e)}')
    
    def serve_cleanup(self):
        """Nettoie le dossier screenshots"""
        try:
            screenshots_dir = "/app/screenshots"
            if not os.path.exists(screenshots_dir):
                screenshots_dir = "./screenshots"
            
            deleted_count = 0
            deleted_files = []
            errors = []
            
            if os.path.exists(screenshots_dir):
                for filename in os.listdir(screenshots_dir):
                    if filename.endswith(('.png', '.wav')) and not filename.startswith('.'):
                        filepath = os.path.join(screenshots_dir, filename)
                        try:
                            os.remove(filepath)
                            deleted_files.append(filename)
                            deleted_count += 1
                        except Exception as e:
                            errors.append(f"{filename}: {str(e)}")
            
            response = {
                'success': True,
                'deleted_count': deleted_count,
                'deleted_files': deleted_files[:10],  # Limiter à 10 pour l'affichage
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }
            
            if errors:
                response['success'] = False
                response['error'] = f"{len(errors)} erreur(s) lors de la suppression"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
            # Log de l'action
            client_ip = self.client_address[0]
            print(f"🗑️ Cleanup par {client_ip}: {deleted_count} fichier(s) supprimé(s)")
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e),
                'deleted_count': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def serve_health(self):
        """Health check public pour Railway"""
        health_data = {
            'status': 'healthy',
            'service': 'screenshot-viewer',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(health_data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Surcharge pour logger les accès"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]
        message = format % args
        print(f"[{timestamp}] {client_ip} - {message}")

def run_screenshot_viewer(port=8081):
    """Lance le serveur de visualisation des screenshots"""
    try:
        # Génération automatique d'un token si non défini
        if not os.getenv('SCREENSHOT_TOKEN'):
            token = secrets.token_urlsafe(32)
            os.environ['SCREENSHOT_TOKEN'] = token
            print(f"🔑 Token auto-généré: {token}")
            print(f"🔗 URL d'accès: http://localhost:{port}/?token={token}")
        
        server = HTTPServer(('', port), ScreenshotViewerHandler)
        print(f"🖼️ Screenshot viewer sécurisé démarré sur :{port}")
        
        # Informations d'authentification
        token = os.getenv('SCREENSHOT_TOKEN')
        username = os.getenv('SCREENSHOT_USERNAME')
        
        if token:
            print(f"🔐 Accès par token: ?token={token}")
        if username:
            print(f"🔐 Accès par basic auth: {username}:***")
        
        # Lancer dans un thread séparé
        def serve_forever():
            server.serve_forever()
        
        thread = threading.Thread(target=serve_forever, daemon=True)
        thread.start()
        
        return server
        
    except Exception as e:
        print(f"❌ Erreur démarrage screenshot viewer: {e}")
        return None

if __name__ == "__main__":
    # Test local
    run_screenshot_viewer()
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur")