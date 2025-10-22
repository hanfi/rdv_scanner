# 🔧 Documentation Technique - Scanner RDV Multimodal

## 🏗️ Architecture Système

### **Stack Technologique**
```
🧠 AI Engine: Google Gemini 2.5 Flash (Multimodal)
🌐 Browser: Playwright + Chromium
🎧 Audio: WAV capture + transcription
🖼️ Image: PNG capture + OCR  
🐍 Runtime: Python 3.12+ + asyncio
📝 Logging: Structured JSON + files
```

### **Modules Principaux**

#### `rdv_scanner_multimodal.py` - Scanner Principal
```python
# Classes principales
class MultimodalRDVScanner:
    - scan_page_with_multimodal()    # Scan avec résolution multimodale
    - navigate_to_captcha()          # Navigation optimisée Cloudflare  
    - capture_media()                # Capture image + audio
    - submit_and_check()             # Soumission + vérification
    - continuous_scan()              # Mode surveillance continu
```

#### `hybrid_optimized_solver_clean.py` - Résolveur Hybride
```python
# Stratégies de résolution
class CaptchaSolver:
    - solve_multimodal()             # Priorité 1: Image + Audio
    - solve_image_only()             # Fallback 2: Image seule
    - solve_audio_only()             # Fallback 3: Audio seul
    - validate_solution()            # Validation croisée
    - get_confidence_level()         # Niveau confiance result
```

#### `multimodal_gemini_solver.py` - Interface Gemini
```python
# Intégration IA multimodale
class MultimodalGeminiSolver:
    - solve_captcha()                # API Gemini 2.5 Flash
    - prepare_multimodal_prompt()    # Prompt engineering optimisé
    - validate_format()              # Validation format réponse
    - handle_api_errors()            # Gestion erreurs API
```

## 🎯 Workflow Technique Détaillé

### **1. Navigation Optimisée**
```python
# Configuration browser optimisée
browser_args = [
    '--disable-blink-features=AutomationControlled',
    '--disable-features=VizDisplayCompositor',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    '--window-size=1366,768',
    '--disable-extensions',
    '--no-sandbox',
    '--disable-dev-shm-usage'
]

# Muting complet si activé
if mute_browser:
    browser_args.extend([
        '--mute-audio',
        '--disable-audio-output',
        '--autoplay-policy=no-user-gesture-required'
    ])
```

### **2. Détection Captcha Robuste**
```python
async def find_captcha_iframe(page):
    """Recherche iframe captcha avec multiples stratégies"""
    selectors = [
        'iframe[src*="captcha"]',
        'iframe[title*="captcha"]', 
        'iframe[name*="captcha"]',
        'iframe[src*="recaptcha"]',
        'frame[src*="captcha"]'
    ]
    
    for selector in selectors:
        iframe = await page.query_selector(selector)
        if iframe:
            return iframe
    
    # Fallback: scroll + recherche
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    # ... retry logic
```

### **3. Capture Multimodale**
```python
async def capture_captcha_media(page, iframe):
    """Capture simultanée image + audio"""
    
    # 1. Capture image haute qualité
    image_buffer = await iframe.screenshot(
        type='png',
        full_page=True,
        quality=100
    )
    
    # 2. Capture audio si présent
    audio_element = await iframe.query_selector('audio')
    if audio_element:
        audio_url = await audio_element.get_attribute('src')
        audio_buffer = await download_audio(audio_url)
        return image_buffer, audio_buffer
    
    return image_buffer, None
```

### **4. Résolution Multimodale Gemini**
```python
def solve_with_gemini_multimodal(image_data, audio_data):
    """Résolution simultanée image + audio"""
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Préparation prompt optimisé
    prompt = """
    CAPTCHA PRÉFECTURE FRANÇAISE - RÉSOLUTION MULTIMODALE
    
    Tu reçois une IMAGE et un AUDIO du même captcha.
    
    INSTRUCTIONS:
    1. Analyse l'IMAGE pour identifier les caractères alphanumériques
    2. Écoute l'AUDIO pour validation/clarification
    3. Compare les deux sources pour éliminer ambiguïtés
    4. Retourne UNIQUEMENT la séquence exacte (6-8 caractères)
    
    CONTRAINTES FORMAT:
    - Lettres MAJUSCULES uniquement
    - Chiffres 0-9 autorisés  
    - Pas d'espaces ni caractères spéciaux
    - Longueur typique: 6-8 caractères
    
    EXEMPLES VALIDES: AB3K7N, M9X4L2, K7V8N4Q3
    """
    
    # Construction contenu multimodal
    content = [prompt]
    
    if image_data:
        content.append({
            'mime_type': 'image/png',
            'data': base64.b64encode(image_data).decode()
        })
    
    if audio_data:
        content.append({
            'mime_type': 'audio/wav', 
            'data': base64.b64encode(audio_data).decode()
        })
    
    response = model.generate_content(content)
    return response.text.strip().upper()
```

## ⚡ Optimisations Performance

### **Gestion Mémoire**
```python
class ResourceManager:
    """Gestion optimisée ressources browser"""
    
    async def __aenter__(self):
        self.browser = await playwright.chromium.launch()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        # Cleanup automatique screenshots anciens
        cleanup_old_files()
```

### **Cache et Persistence**
```python
# Cache résultats pour éviter re-calculs
@lru_cache(maxsize=100)
def validate_captcha_format(solution: str) -> bool:
    """Cache validation format pour performance"""
    pattern = r'^[A-Z0-9]{6,8}$'
    return bool(re.match(pattern, solution))
```

### **Retry Logic Intelligent**
```python
async def retry_with_backoff(operation, max_retries=3):
    """Retry exponentiel avec jitter"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Backoff exponentiel + jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

## 🔐 Sécurité et Robustesse

### **Détection Anti-Bot**
```python
# Simulation comportement humain
async def human_like_interaction(page):
    """Simulation pattern humain"""
    
    # Mouvement souris aléatoire
    await page.mouse.move(
        random.randint(100, 500),
        random.randint(100, 400)
    )
    
    # Délais variables
    await page.wait_for_timeout(random.randint(500, 2000))
    
    # Scroll naturel
    await page.evaluate("""
        window.scrollTo({
            top: Math.random() * 500,
            behavior: 'smooth'
        })
    """)
```

### **Gestion Erreurs Robuste**
```python
class CaptchaError(Exception):
    """Erreurs spécifiques captcha"""
    pass

class NavigationError(Exception):
    """Erreurs navigation"""
    pass

async def safe_operation(operation, error_type=Exception):
    """Wrapper sécurisé opérations"""
    try:
        return await operation()
    except error_type as e:
        logger.error(f"Operation failed: {e}")
        # Capture screenshot debug
        await capture_error_screenshot()
        raise
```

## 📊 Monitoring et Observabilité

### **Logging Structuré**
```python
import structlog

logger = structlog.get_logger()

# Log avec contexte riche
logger.info(
    "captcha_resolved",
    method="multimodal",
    confidence="high",
    attempts=1,
    duration_ms=1250,
    solution_length=8
)
```

### **Métriques Performance**
```python
class PerformanceTracker:
    """Tracking métriques système"""
    
    def __init__(self):
        self.metrics = {
            'total_scans': 0,
            'successful_captchas': 0,
            'multimodal_success': 0,
            'fallback_usage': 0,
            'avg_response_time': 0.0
        }
    
    def record_success(self, method: str, duration: float):
        self.metrics['total_scans'] += 1
        self.metrics['successful_captchas'] += 1
        
        if method == 'multimodal':
            self.metrics['multimodal_success'] += 1
        else:
            self.metrics['fallback_usage'] += 1
            
        # Moving average response time
        self.update_avg_response_time(duration)
```

## 🧪 Tests et Validation

### **Tests Unitaires**
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestCaptchaSolver:
    
    @pytest.mark.asyncio
    async def test_multimodal_resolution(self):
        """Test résolution multimodale"""
        solver = CaptchaSolver()
        
        # Mock Gemini response
        with patch('gemini_solver.solve') as mock_solve:
            mock_solve.return_value = 'AB3K7N'
            
            result = await solver.solve_multimodal(
                image_data=b'fake_image',
                audio_data=b'fake_audio'
            )
            
            assert result == 'AB3K7N'
            assert solver.confidence_level == 'high'
    
    def test_format_validation(self):
        """Test validation format"""
        assert validate_captcha_format('AB3K7N') == True
        assert validate_captcha_format('ab3k7n') == False
        assert validate_captcha_format('AB3K7N!') == False
```

### **Tests d'Intégration**
```python
@pytest.mark.integration
async def test_full_scan_workflow():
    """Test workflow complet"""
    scanner = MultimodalRDVScanner()
    
    # Test avec page mockée
    result = await scanner.scan_page_with_multimodal(
        url='https://test-prefecture.local'
    )
    
    assert result['status'] == 'SUCCESS'
    assert 'captcha_solution' in result
    assert result['confidence'] in ['high', 'medium', 'low']
```

## 🚀 Déploiement et Production

### **Configuration Production**
```python
# .env production
ENVIRONMENT=production
LOG_LEVEL=INFO
HEADLESS=true
CHECK_INTERVAL=300
MAX_CONCURRENT_PAGES=2
RETRY_ATTEMPTS=3
TIMEOUT_SECONDS=30
```

### **Monitoring Production**
```python
# Health check endpoint
async def health_check():
    """Vérification santé système"""
    checks = {
        'gemini_api': await test_gemini_connection(),
        'browser': await test_browser_launch(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    all_healthy = all(checks.values())
    return {'status': 'healthy' if all_healthy else 'degraded', 'checks': checks}
```

### **Cleanup Automatique**
```bash
# Cron job nettoyage
0 2 * * * /usr/local/bin/cleanup_scanner.sh

#!/bin/bash
# cleanup_scanner.sh
cd /path/to/scanner
find screenshots/ -name "*.png" -mtime +7 -delete
find . -name "*.log" -mtime +30 -delete
```

## 📈 Optimisations Futures

### **Améliorations Prévues**
1. **Cache Redis** : Mise en cache résultats captcha
2. **Queue Système** : Traitement asynchrone multiple pages
3. **Load Balancing** : Distribution charge multi-instances
4. **ML Pipeline** : Apprentissage patterns captcha
5. **API GraphQL** : Interface flexible requêtes

### **Roadmap Technique**
- **Q1 2024** : Cache distribué + API REST
- **Q2 2024** : ML training + prédictions
- **Q3 2024** : Scaling horizontal + orchestration
- **Q4 2024** : Edge computing + CDN integration

---

**🔧 Documentation maintenue par GitHub Copilot - Architecture évolutive et maintenable !**