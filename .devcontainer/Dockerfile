# Image DevContainer Python simple
FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

# Variables d'environnement
ENV PYTHONPATH=/workspaces/rdv_scanner

# Installation des dépendances Python du projet
RUN pip install --no-cache-dir \
        playwright \
        python-dotenv \
        requests \
        google-generativeai \
        beautifulsoup4 \
        twocaptcha

# Installation du navigateur Playwright (seule installation navigateur nécessaire)
RUN playwright install chromium --with-deps

# Configuration du workspace
WORKDIR /workspaces/rdv_scanner