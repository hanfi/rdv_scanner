# Utilisation de l'image Python officielle avec DevContainer
FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

# Métadonnées
LABEL maintainer="GitHub Copilot"
LABEL description="DevContainer pour Scanner RDV Multimodal avec Playwright"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONPATH=/workspaces/rdv_scanner
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0

# Installation des dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    # Dépendances de base
    wget \
    gnupg \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    curl \
    lsb-release \
    # Dépendances pour l'affichage et les navigateurs
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
    xdg-utils \
    # Outils de développement
    git \
    make \
    vim \
    nano \
    htop \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Installation de Google Chrome (pour Playwright)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation d'outils Python utiles
RUN python -m pip install --upgrade pip \
    && pip install \
        black \
        pylint \
        mypy \
        pytest \
        ipython \
        jupyter

# Configuration du workspace
WORKDIR /workspaces/rdv_scanner

# Exposition des ports pour le développement
EXPOSE 8000 3000 5000

# Commande par défaut
CMD ["bash"]