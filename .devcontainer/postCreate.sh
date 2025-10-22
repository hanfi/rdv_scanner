#!/bin/bash

# 🎯 Script de post-création DevContainer pour RDV Scanner Multimodal
echo "🚀 Configuration de l'environnement RDV Scanner..."

# Mise à jour du système
sudo apt-get update && sudo apt-get upgrade -y

# Installation des dépendances système pour Playwright
echo "📦 Installation des dépendances système..."
sudo apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    curl \
    lsb-release \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils

# Installation de Google Chrome pour Playwright
echo "🌐 Installation de Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Mise à jour pip
echo "🐍 Mise à jour de pip..."
python -m pip install --upgrade pip

# Installation des dépendances Python
echo "📚 Installation des dépendances Python..."
pip install -r requirements.txt

# Installation des navigateurs Playwright
echo "🎭 Installation des navigateurs Playwright..."
playwright install chromium
playwright install-deps chromium

# Configuration des permissions pour screenshots
echo "📸 Configuration du répertoire screenshots..."
mkdir -p screenshots
chmod 755 screenshots

# Copie du template de configuration
echo "⚙️ Configuration des variables d'environnement..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Fichier .env créé à partir du template"
    echo "⚠️  N'oubliez pas de configurer votre GEMINI_API_KEY dans .env"
else
    echo "✅ Fichier .env existant conservé"
fi

# Configuration Git
echo "📝 Configuration Git..."
git config --global init.defaultBranch main
git config --global pull.rebase false

# Affichage des informations utiles
echo ""
echo "🎉 Configuration terminée !"
echo ""
echo "📋 Commandes utiles :"
echo "  ./run_scanner.sh          - Interface interactive"
echo "  python scanner.py --once  - Test unique"
echo "  python scanner.py --continuous - Mode continu"
echo ""
echo "⚙️  N'oubliez pas de configurer votre GEMINI_API_KEY dans .env"
echo "🔗 Obtenir une clé: https://makersuite.google.com/app/apikey"
echo ""
echo "🚀 Projet prêt pour le développement !"