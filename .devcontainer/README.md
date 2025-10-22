# 🐳 DevContainer Configuration

Ce projet inclut une configuration DevContainer complète pour un environnement de développement standardisé et reproductible.

## 🚀 Démarrage Rapide

### **Méthode 1: GitHub Codespaces** 
1. Aller sur le repository GitHub
2. Cliquer sur "Code" → "Codespaces" → "Create codespace"
3. Attendre la création automatique de l'environnement
4. Configuration automatique via `postCreate.sh`

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

## 🔧 Post-Installation Automatique

Le script `postCreate.sh` configure automatiquement :

✅ **Dépendances système** : Chrome, drivers Playwright  
✅ **Environnement Python** : Installation des requirements  
✅ **Navigateurs** : Chromium pour Playwright  
✅ **Configuration** : Template .env créé  
✅ **Permissions** : Répertoire screenshots configuré  

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
2. **Dépendances** : Modifier `.devcontainer/postCreate.sh`
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