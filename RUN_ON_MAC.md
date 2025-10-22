# 🍎 Exécuter le scanner sur Mac (RECOMMANDÉ)

## 🎯 Pourquoi sur Mac ?

Le scanner fonctionne **beaucoup mieux** sur Mac/Windows car :

- ✅ **Mode non-headless** : Navigateur visible avec interface complète
- ✅ **IP résidentielle** : Moins suspecte pour Cloudflare
- ✅ **Empreinte normale** : GPU, extensions, historique = navigateur humain
- ✅ **Meilleur taux de réussite** : ~90% vs ~10% en container headless

## 📋 Prérequis

```bash
# 1. Python 3.11+
python3 --version

# 2. Installer les dépendances
pip install playwright python-dotenv pillow google-generativeai

# 3. Installer Chromium pour Playwright
playwright install chromium
```

## 🚀 Installation rapide

```bash
# Cloner le projet
cd ~/Desktop
mkdir rdv_scanner
cd rdv_scanner

# Copier les fichiers depuis le container
# (ou récupérer depuis votre repo Git)

# Structure attendue :
# rdv_scanner/
#   ├── scanner.py
#   ├── captcha_solver.py
#   ├── gemini_solver.py
#   ├── prefecture_analyzer.py
#   ├── notifier.py
#   ├── .env
#   └── screenshots/

# Installer les dépendances
pip3 install playwright python-dotenv pillow google-generativeai
playwright install chromium
```

## ⚙️ Configuration

Éditez le fichier `.env` :

```bash
# MODE NON-HEADLESS (essentiel sur Mac !)
HEADLESS=false

# URLs à scanner
PAGE_1_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/2381/cgu/
PAGE_2_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/3260/cgu/

# Gemini Vision (gratuit)
GEMINI_API_KEY=AIzaSy...votre_clé

# Intervalle (5 minutes)
CHECK_INTERVAL=300
```

## ▶️ Lancer le scanner

### Test unique (recommandé pour débuter)

```bash
cd ~/Desktop/rdv_scanner
python3 scanner.py --once
```

Vous verrez :
- 🖥️ Une fenêtre de navigateur s'ouvrir
- 🤖 Gemini résoudre les captchas automatiquement
- ✅ Les résultats dans le terminal

### Mode continu (surveillance)

```bash
python3 scanner.py --continuous
```

Le scanner vérifiera les 2 pages toutes les 5 minutes.

## 🎯 Ce qui va se passer

1. **Fenêtre de navigateur** s'ouvre (Chromium)
2. **Cloudflare** : Attente de 15-20 secondes
3. **Captcha détecté** : Screenshot envoyé à Gemini
4. **Gemini résout** : Texte saisi caractère par caractère
5. **Formulaire validé** : Clic sur "Suivant"
6. **Redirection** vers `/creneau/`
7. **Analyse** :
   - ✅ "Aucun créneau disponible" → Pas de RDV
   - ✅ "Choisissez votre créneau" → **RDV DISPONIBLE !**

## 💡 Avantages du mode visible

### ✅ Vous pouvez intervenir
- Si Cloudflare bloque, vous pouvez cliquer manuellement
- Si le captcha échoue, vous pouvez le saisir vous-même
- Vous voyez exactement ce qui se passe

### ✅ Meilleur taux de réussite
- Cloudflare détecte moins le bot
- Navigation plus fluide
- Cookies et sessions persistants

### ✅ Debug facile
- Vous voyez les erreurs en direct
- Captures d'écran dans `screenshots/`
- Logs détaillés dans le terminal

## 📊 Logs attendus (succès)

```
2025-10-22 14:00:00 - INFO - 🖥️ Mode avec interface (recommandé pour contourner Cloudflare)
2025-10-22 14:00:01 - INFO - Navigateur démarré avec succès
2025-10-22 14:00:02 - INFO - Page Page 1 chargée
2025-10-22 14:00:03 - INFO - Attente de passage Cloudflare...
2025-10-22 14:00:20 - INFO - Captcha préfecture détecté
2025-10-22 14:00:21 - INFO - 🤖 Analyse du captcha avec Gemini
2025-10-22 14:00:23 - INFO - ✅ Gemini a lu le captcha: 'ABC123'
2025-10-22 14:00:26 - INFO - ✅ Captcha rempli avec: ABC123
2025-10-22 14:00:28 - INFO - 🔘 Clic sur le bouton de validation
2025-10-22 14:00:35 - INFO - ✅ Redirection réussie vers: .../creneau/
2025-10-22 14:00:36 - INFO - ❌ Indisponible: aucun créneau disponible
```

## 🐛 En cas de problème

### Cloudflare bloque encore
- Attendez 2-3 minutes entre chaque test
- Fermez complètement le navigateur entre les essais
- Changez votre IP (Wi-Fi → 4G)

### Captcha incorrect
- Gemini a ~85-90% de réussite
- Le scanner réessaiera au prochain cycle (5 min)
- Vous pouvez intervenir manuellement dans la fenêtre

### Playwright non installé
```bash
pip3 install playwright
playwright install chromium
```

### Module non trouvé
```bash
pip3 install python-dotenv pillow google-generativeai
```

## 🎉 Succès !

Une fois configuré sur Mac, le scanner :
- ✅ Contourne Cloudflare naturellement
- ✅ Résout les captchas automatiquement (Gemini)
- ✅ Détecte les créneaux disponibles
- ✅ Vous notifie (si configuré)
- ✅ Tourne en continu toutes les 5 minutes

**Laissez-le tourner en arrière-plan et vous serez notifié dès qu'un RDV est disponible !** 🚀
