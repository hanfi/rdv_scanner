# Dockerfile pour déploiement cloud
FROM python:3.11-slim

# Installer les dépendances système + Xvfb pour display virtuel
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright et Chromium
RUN playwright install chromium
RUN playwright install-deps chromium

# Copier le code source
COPY . .

# Créer le dossier screenshots
RUN mkdir -p screenshots

# Variables d'environnement par défaut (NON-HEADLESS pour contourner Cloudflare)
ENV HEADLESS=false
ENV MUTE_BROWSER=true
ENV BACKGROUND_MODE=true
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV XVFB_WHD=1366x768x24

# Port pour health check et screenshot viewer
EXPOSE 8080 8081

# Script de démarrage avec display virtuel
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Commande par défaut avec Xvfb
CMD ["/start.sh"]