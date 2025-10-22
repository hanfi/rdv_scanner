# RDV Scanner - Préfecture

> **⚠️ DISCLAIMER ⚠️**  
> Ce projet a été entièrement développé par **GitHub Copilot** (Assistant IA basé sur Claude Sonnet 4) en collaboration avec l'utilisateur. Le code, l'architecture, les optimisations multimodales et la documentation ont été générés automatiquement par l'IA. Cette solution représente l'état de l'art en matière d'automatisation intelligente et de résolution de captchas multimodaux.

Scanner automatisé pour vérifier la disponibilité de rendez-vous sur les pages de la préfecture avec détection et gestion de captcha.

## ✅ Fonctionnalités

- ✨ Navigation automatique avec contournement Cloudflare
- 🔍 Détection automatique des captchas
- 📸 Capture automatique des captchas pour résolution manuelle ou automatique
- 🔔 Notifications en cas de disponibilité
- 📊 Logs détaillés et captures d'écran
- ⏰ Mode continu avec vérifications périodiques

## 🎯 Pages surveillées

Les deux URLs configurées :
1. https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/2381/cgu/
2. https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/3260/cgu/

## 📋 Installation

```bash
cd /app/rdv_scanner

# Installer les dépendances
pip install -r requirements.txt

# Installer Chromium pour Playwright
playwright install chromium
playwright install-deps chromium
```

## ⚙️ Configuration

Le fichier `.env` est déjà configuré avec les bonnes URLs. Vous pouvez personnaliser :

```bash
# Intervalle entre les vérifications (en secondes)
CHECK_INTERVAL=300  # 5 minutes par défaut

# API de résolution de captcha (optionnel mais recommandé)
CAPTCHA_API_KEY=votre_clé_api_2captcha
CAPTCHA_SERVICE=2captcha

# Webhook pour notifications (optionnel)
NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/VOTRE/WEBHOOK
```

### 🔑 Service de résolution de captcha (recommandé)

Pour résoudre automatiquement les captchas mathématiques :

1. Créez un compte sur [2captcha.com](https://2captcha.com)
2. Ajoutez votre clé API dans `.env` : `CAPTCHA_API_KEY=votre_clé`
3. Le scanner résoudra automatiquement les captchas

**Sans clé API** : Les captchas sont détectés et capturés dans `screenshots/captcha_*.png` pour résolution manuelle.

## 🚀 Utilisation

### Mode unique (une vérification)

```bash
python scanner.py --once
```

### Mode continu (vérifications automatiques)

```bash
python scanner.py --continuous
```

### En arrière-plan

```bash
# Avec nohup
nohup python scanner.py --continuous > output.log 2>&1 &

# Voir les logs en temps réel
tail -f scanner.log

# Arrêter le scanner
pkill -f scanner.py
```

### Avec Make

```bash
make run-once    # Une seule vérification
make run         # Mode continu
```

## 📂 Structure des fichiers

```
/app/rdv_scanner/
├── scanner.py              # Script principal
├── captcha_solver.py       # Résolution de captcha
├── prefecture_analyzer.py  # Analyse spécifique préfecture
├── notifier.py            # Système de notifications
├── .env                   # Configuration (déjà prêt)
├── requirements.txt       # Dépendances Python
├── scanner.log           # Logs d'exécution
└── screenshots/          # Captures d'écran et captchas
    ├── page_1_initial_*.png      # Captures des pages
    ├── page_2_initial_*.png
    └── captcha_cgu.png           # Captcha capturé
```

## 📊 Logs et résultats

- **Logs** : `scanner.log` (rotation automatique)
- **Captures** : `screenshots/` (full page + captchas)
- **Console** : Affichage en temps réel

### Exemple de sortie

```
2025-10-22 12:35:37 - INFO - Captcha préfecture détecté
2025-10-22 12:35:38 - INFO - Captcha capturé: screenshots/captcha_cgu.png
2025-10-22 12:35:40 - INFO - ✅ Page 1: Rendez-vous disponible!
2025-10-22 12:35:42 - INFO - ❌ Page 2: Pas de rendez-vous disponible
```

## 🎯 Résolution manuelle du captcha

Si vous n'avez pas configuré de clé API :

1. Le scanner capture le captcha dans `screenshots/captcha_cgu.png`
2. Ouvrez l'image pour voir le calcul mathématique
3. Le scanner attend actuellement un service automatique

**Pour activer la résolution manuelle en mode interactif** : Mettez `HEADLESS=false` et le scanner attendra 30 secondes que vous entriez le captcha manuellement dans le navigateur (nécessite un serveur X).

## 🔧 Scripts utiles

### Analyser une page

```bash
python analyze_page.py  # Analyse la page avec extraction complète
```

### Tester le captcha

```bash
python test_captcha.py  # Test détaillé de la détection de captcha
```

## 🐛 Dépannage

### Le scanner est bloqué par Cloudflare

✅ **Déjà résolu** : Le scanner attend automatiquement 8 secondes pour passer Cloudflare.

### Le captcha n'est pas détecté

✅ **Déjà résolu** : Le scanner scrolle et détecte le champ `captchaUsercode`.

### Erreur "Target page has been closed"

- Vous êtes en mode `HEADLESS=false` dans un environnement sans interface graphique
- Solution : Mettez `HEADLESS=true` dans `.env`

### Les rendez-vous ne sont pas détectés

- Vérifiez les captures d'écran dans `screenshots/`
- Consultez `scanner.log` pour plus de détails
- Les pages peuvent vraiment être complètes

## 📱 Notifications

### Slack/Discord

Configurez `NOTIFICATION_WEBHOOK` dans `.env` avec votre webhook URL :

```bash
NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Le scanner enverra automatiquement une notification quand un RDV est disponible.

## 🔄 Mise à jour des URLs

Pour surveiller d'autres démarches, éditez `.env` :

```bash
PAGE_1_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/XXXX/cgu/
PAGE_2_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/YYYY/cgu/
```

## ⚡ Performance

- **Intervalle recommandé** : 300 secondes (5 minutes)
- **Durée par vérification** : ~20-30 secondes (2 pages + Cloudflare)
- **Consommation** : Faible (mode headless)

## 🎓 Développement

Le code est modulaire et extensible :

- `scanner.py` : Logique principale
- `captcha_solver.py` : Ajoutez d'autres types de captcha
- `prefecture_analyzer.py` : Logique spécifique aux pages préfecture
- `notifier.py` : Ajoutez d'autres canaux de notification

## 📝 Licence

Ce scanner est fourni à des fins éducatives. Respectez les conditions d'utilisation des sites web que vous scannez.
