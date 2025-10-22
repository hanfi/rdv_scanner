#!/bin/bash
# Script de lancement du scanner RDV optimisé

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"
SCANNER_SCRIPT="$SCRIPT_DIR/rdv_scanner_multimodal.py"
LEGACY_SCANNER="$SCRIPT_DIR/rdv_scanner_final.py"

# Fonction d'affichage avec couleur
print_color() {
    printf "${2}${1}${NC}\n"
}

# Vérification de l'environnement virtuel
if [ ! -d "$VENV_PATH" ]; then
    print_color "❌ Environnement virtuel non trouvé dans $VENV_PATH" $RED
    print_color "🔧 Créez l'environnement avec: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" $YELLOW
    exit 1
fi

# Vérification du fichier .env
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    print_color "❌ Fichier .env non trouvé" $RED
    print_color "🔧 Créez le fichier .env avec les variables nécessaires" $YELLOW
    exit 1
fi

# Affichage du menu
print_color "🎯 Scanner RDV Préfecture - Version Multimodale Avancée" $BLUE
print_color "=======================================================" $BLUE
echo ""
print_color "Choisissez une option:" $GREEN
echo "1) � Test unique MULTIMODAL (un scan puis arrêt)"
echo "2) 🔄 Mode continu MULTIMODAL (scans répétés)"
echo "3) �️  Test unique LEGACY (image seule)"
echo "4) �📋 Voir les logs"
echo "5) 🧹 Nettoyer les screenshots"
echo "6) ❌ Quitter"
echo ""

read -p "Votre choix (1-6): " choice

case $choice in
    1)
        echo "🔥 Lancement test unique multimodal..."
        python scanner.py --once
        ;;
    2)
        echo "🔄 Lancement mode continu multimodal..."
        python scanner.py --continuous
        ;;
    3)
        print_color "🖼️ Lancement du scanner legacy (image seule)..." $GREEN
        "$VENV_PATH/bin/python" "$LEGACY_SCANNER" --once
        ;;
    4)
        if [ -f "scanner.log" ]; then
            echo "📋 Affichage des logs récents..."
            tail -50 scanner.log
        elif [ -f "$SCRIPT_DIR/rdv_scanner.log" ]; then
            print_color "📋 Dernières lignes du log legacy:" $GREEN
            tail -50 "$SCRIPT_DIR/rdv_scanner.log"
        else
            echo "❌ Aucun fichier de log trouvé (scanner.log)"
        fi
        ;;
    5)
        if [ -d "$SCRIPT_DIR/screenshots" ]; then
            screenshot_count=$(find "$SCRIPT_DIR/screenshots" -name "*.png" -o -name "*.wav" | wc -l)
            if [ $screenshot_count -gt 0 ]; then
                print_color "🧹 Suppression de $screenshot_count fichiers..." $YELLOW
                rm -f "$SCRIPT_DIR/screenshots"/*.png "$SCRIPT_DIR/screenshots"/*.wav
                print_color "✅ Screenshots et audios supprimés" $GREEN
            else
                print_color "📂 Aucun fichier à supprimer" $YELLOW
            fi
        else
            print_color "📂 Dossier screenshots non trouvé" $YELLOW
        fi
        ;;
    6)
        print_color "👋 Au revoir!" $BLUE
        exit 0
        ;;
    *)
        print_color "❌ Option invalide" $RED
        exit 1
        ;;
esac