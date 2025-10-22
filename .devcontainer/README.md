# 🐳 DevContainer Configuration

# DevContainer pour RDV Scanner Multimodal

## 📝 Description

Ce DevContainer permet de développer le Scanner RDV Multimodal dans un environnement Docker standardisé avec toutes les dépendances pré-installées.

## 🚀 Fonctionnalités

### Technologies Incluses
- **Python 3.12** avec environnement virtuel configuré
- **Playwright** avec navigateur Chromium pour l'automatisation web
- **Outils de développement** : Black, Pylint, MyPy, Pytest
- **Jupyter** pour l'exploration de données
- **Extensions VS Code** pré-configurées pour un développement optimal

### Dépendances Principales
- `playwright` - Automatisation de navigateurs
- `google-generativeai` - Intégration Gemini 2.5 Flash
- `beautifulsoup4` - Parsing HTML
- `twocaptcha` - Résolution de captchas
- `python-dotenv` - Gestion des variables d'environnement
- `requests` - Client HTTP

## 🛠 Utilisation

### Avec VS Code et l'extension Dev Containers

1. **Installer l'extension** : [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Ouvrir dans DevContainer** :
   - Ouvrir le dossier dans VS Code
   - Appuyer sur `Ctrl+Shift+P` (ou `Cmd+Shift+P`)
   - Taper "Dev Containers: Reopen in Container"
   - Sélectionner et attendre la construction

3. **Développer** :
   - Tous les outils sont pré-installés
   - Extensions VS Code configurées automatiquement
   - Terminal intégré avec environnement Python complet

### Avec GitHub Codespaces

1. **Créer un Codespace** depuis le repository GitHub
2. **Attendre la construction** (environ 2-3 minutes)
3. **Commencer à développer** immédiatement

### Build Manuel Docker

```bash
# Construction de l'image
docker build -t rdv-scanner-dev .devcontainer/

# Exécution avec volume
docker run -it --rm \
  -v "$(pwd)":/workspaces/rdv_scanner \
  -w /workspaces/rdv_scanner \
  rdv-scanner-dev bash
```

## 🔧 Configuration

### Variables d'Environnement
Créer un fichier `.env` dans le répertoire racine :
```env
GEMINI_API_KEY=votre_cle_api_gemini
TWOCAPTCHA_API_KEY=votre_cle_twocaptcha
```

### Ports Exposés
- `8000` - Serveur de développement (Django/FastAPI)
- `3000` - Serveur frontend
- `5000` - Flask/Streamlit

## 📦 Extensions VS Code Incluses

- **Python** : Support complet Python avec IntelliSense
- **GitHub Copilot** : Assistance IA pour le code
- **Pylint** : Analyse statique de code
- **Black Formatter** : Formatage automatique Python
- **Thunder Client** : Client REST pour tester les APIs
- **GitLens** : Intégration Git avancée
- **Auto Docstring** : Génération automatique de docstrings
- **Path Intellisense** : Autocomplétion des chemins de fichiers

## 🏗 Architecture DevContainer

```
.devcontainer/
├── devcontainer.json    # Configuration VS Code DevContainer
├── Dockerfile           # Image Docker personnalisée
└── README.md           # Cette documentation
```

### Dockerfile Highlights
- **Base** : Image Microsoft DevContainer Python 3.12
- **Navigateur** : Chromium pour compatibilité multi-architecture
- **Optimisations** : Cache pip, installation en parallèle
- **Sécurité** : Environnement non-root, dépendances sécurisées

## 🐛 Dépannage

### Problèmes Courants

#### DevContainer ne démarre pas
```bash
# Reconstruire sans cache
docker build --no-cache -t rdv-scanner-dev .devcontainer/
```

#### Erreur Playwright/Chromium
```bash
# Dans le container
playwright install chromium
```

#### Permissions de fichiers
```bash
# Corriger les permissions (sur l'hôte)
sudo chown -R $USER:$USER .
```

## 📊 Performance

### Temps de Build
- **Premier build** : ~3-5 minutes
- **Builds suivants** : ~10-30 secondes (avec cache)
- **Démarrage DevContainer** : ~15-30 secondes

### Ressources Recommandées
- **RAM** : 2 GB minimum, 4 GB recommandé
- **CPU** : 2 cores minimum
- **Stockage** : 2 GB pour l'image + 1 GB pour les dépendances

## 🔄 Mise à Jour

Pour mettre à jour l'environnement :
```bash
# Reconstruire l'image
docker build --no-cache -t rdv-scanner-dev .devcontainer/

# Ou dans VS Code : "Dev Containers: Rebuild Container"
```

## 🤝 Contribution

1. Modifier `.devcontainer/devcontainer.json` pour les extensions
2. Modifier `.devcontainer/Dockerfile` pour les dépendances système
3. Tester le build localement avant de commit
4. Documenter les changements dans ce README

## 📚 Liens Utiles

- [Documentation Dev Containers](https://containers.dev/)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces](https://github.com/features/codespaces)
- [Playwright Docker](https://playwright.dev/docs/docker)

## 🚀 Démarrage Rapide

### **Méthode 1: GitHub Codespaces** 
1. Aller sur le repository GitHub
2. Cliquer sur "Code" → "Codespaces" → "Create codespace"
3. Attendre la création automatique de l'environnement
4. Configuration automatique via Dockerfile + postCreateCommand

### **Méthode 2: VS Code Local**
1. Installer l'extension "Dev Containers" dans VS Code
2. Ouvrir le projet avec `code .`
3. VS Code détectera automatiquement la config DevContainer
4. Cliquer sur "Reopen in Container" dans la notification

### **Méthode 3: CLI Docker**
```bash
# Cloner le repository
git clone https://github.com/hanfi/rdv_scanner.git
cd rdv_scanner

# Construire et lancer le container
docker build -t rdv-scanner-dev .devcontainer
docker run -it --rm -v $(pwd):/workspace rdv-scanner-dev
```

## 🛠️ Configuration Incluse

### **🐍 Environnement Python**
- **Python 3.12** avec toutes les dépendances
- **Playwright** avec navigateurs installés
- **Extensions VS Code** optimisées pour Python

### **📦 Extensions VS Code Pré-installées**
- `ms-python.python` - Support Python complet
- `ms-python.black-formatter` - Formatage automatique
- `ms-python.pylint` - Linting et qualité code
- `ms-toolsai.jupyter` - Support Jupyter notebooks
- `GitHub.copilot` - GitHub Copilot AI
- `GitHub.copilot-chat` - Chat avec Copilot

### **⚙️ Configuration Automatique**
- **Thème clair** : GitHub Light Default
- **Formatage automatique** : Black formatter sur sauvegarde
- **Linting actif** : Pylint avec règles optimisées
- **Git configuré** : Branche main par défaut

### **🌐 Ports Exposés**
- `8000` - Serveur web principal
- `3000` - Serveur de développement
- `5000` - Serveur Flask (si nécessaire)

## 🔧 Configuration Automatique

Le Dockerfile configure automatiquement :

✅ **Environnement Python 3.12** : Avec pip, black, pylint, mypy  
✅ **Dépendances système** : Chrome, drivers Playwright  
✅ **Navigateurs Playwright** : Chromium pré-installé  
✅ **Outils développement** : Git, nano, vim, htop, tree  

Le postCreateCommand ajoute :
✅ **Dépendances projet** : Installation via requirements.txt  
✅ **Configuration** : Template .env créé automatiquement  

## 🎯 Utilisation

Une fois le container lancé :

```bash
# Configuration de la clé API (obligatoire)
nano .env  # Ajouter votre GEMINI_API_KEY

# Interface interactive
./run_scanner.sh

# Tests directs
python scanner.py --once
python scanner.py --continuous
```

## 🔐 Variables d'Environnement

Le container est configuré avec :
- `PYTHONPATH` pointant vers le workspace
- `DISPLAY` pour l'affichage X11 (si nécessaire)
- `DEBIAN_FRONTEND=noninteractive` pour l'installation silencieuse

## 🛡️ Avantages DevContainer

### **🔄 Reproductibilité**
- Environnement identique pour tous les développeurs
- Pas de "ça marche sur ma machine"
- Configuration versionnée avec le code

### **⚡ Rapidité**
- Setup automatique en une commande
- Toutes les dépendances pré-installées
- Prêt à coder en minutes

### **🎯 Isolation**
- Pas d'impact sur le système host
- Environnement dédié au projet
- Nettoyage facile

### **☁️ Cloud Ready**
- Compatible GitHub Codespaces
- Développement dans le cloud
- Accès depuis n'importe où

## 🔧 Personnalisation

Pour modifier la configuration :

1. **Extensions** : Éditer `.devcontainer/devcontainer.json`
2. **Dépendances** : Modifier `.devcontainer/Dockerfile`
3. **Settings VS Code** : Ajuster la section `settings`

## 📋 Commandes Utiles

```bash
# Rebuild du container (si config modifiée)
# Command Palette → "Dev Containers: Rebuild Container"

# Logs de création
# Voir l'onglet "Terminal" lors du setup

# Accès au container
# Terminal → New Terminal (déjà dans le container)
```

## 🎉 Résultat

Avec cette configuration, vous obtenez un environnement de développement complet et optimisé pour le scanner RDV multimodal, incluant :

- ✅ Python 3.12 + toutes dépendances
- ✅ Playwright avec navigateurs  
- ✅ VS Code configuré avec extensions
- ✅ Git setup + GitHub CLI
- ✅ Thème clair et settings optimisés
- ✅ Scripts de lancement prêts

**🚀 Développement streamliné et professionnel !**