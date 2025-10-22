.PHONY: install setup run run-once help clean

help:
	@echo "Commandes disponibles:"
	@echo "  make install    - Installer les dépendances"
	@echo "  make setup      - Configuration initiale"
	@echo "  make run        - Lancer le scanner en mode continu"
	@echo "  make run-once   - Lancer le scanner une seule fois"
	@echo "  make clean      - Nettoyer les fichiers temporaires"

install:
	pip install -r requirements.txt
	playwright install chromium

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Fichier .env créé. Configurez-le avant de lancer le scanner."; \
	else \
		echo "Le fichier .env existe déjà."; \
	fi
	@mkdir -p screenshots logs

run:
	python scanner.py --continuous

run-once:
	python scanner.py --once

clean:
	rm -rf __pycache__ .pytest_cache
	rm -f *.log
	find . -name "*.pyc" -delete
