#!/bin/bash
# Script de démarrage avec display virtuel pour contourner Cloudflare

echo "🚀 Démarrage du scanner RDV avec display virtuel..."

# Démarrer Xvfb (serveur X virtuel) en arrière-plan
echo "🖥️  Démarrage du display virtuel Xvfb..."
# Profondeur 16 bits (vs 24) = ~30 % de mémoire framebuffer en moins,
# critique dans un conteneur limité à 1 GB de RAM.
Xvfb :99 -screen 0 "${XVFB_WHD:-1366x768x16}" -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Attendre que Xvfb soit prêt
sleep 2

# Optionnel: Démarrer un gestionnaire de fenêtres léger
echo "🪟 Démarrage du gestionnaire de fenêtres..."
fluxbox -display :99 &
FLUXBOX_PID=$!

# Vérifier que le display fonctionne
echo "✅ Vérification du display virtuel..."
export DISPLAY=:99
xdpyinfo > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Display virtuel :99 opérationnel"
else
    echo "❌ Erreur display virtuel"
    exit 1
fi

# Fonction de nettoyage à l'arrêt
cleanup() {
    echo "🧹 Nettoyage des processus..."
    kill $XVFB_PID $FLUXBOX_PID 2>/dev/null
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGTERM SIGINT

# Démarrer le scanner principal
echo "🎯 Lancement du scanner RDV (mode non-headless avec display virtuel)..."
python scanner.py --continuous &
SCANNER_PID=$!

# Attendre le processus principal
wait $SCANNER_PID

# Nettoyage final
cleanup