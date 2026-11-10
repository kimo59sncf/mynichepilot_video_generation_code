#!/usr/bin/env bash
# =============================================================================
# MyNichePilot - Script Shell d'Exécution Complète du Pipeline Vidéo
# =============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "======================================================================="
echo "  🎬 MyNichePilot Video Generator — Lanceur Automatique de Production"
echo "======================================================================="

# 1. Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Erreur : Python 3 n'est pas installé sur votre système."
    exit 1
fi
echo "✓ Python 3 détecté : $(python3 --version)"

# 2. Vérification de FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Erreur : FFmpeg n'est pas installé ou introuvable dans le PATH."
    echo "   Installez FFmpeg : 'sudo apt install ffmpeg' (Debian/Ubuntu) ou 'brew install ffmpeg' (macOS)"
    exit 1
fi
echo "✓ FFmpeg détecté : $(ffmpeg -version | head -n 1)"

# 3. Installation des dépendances Python si nécessaire
echo ""
echo "📦 Vérification des dépendances Python requises..."
python3 -c "import edge_tts, PIL, numpy, scipy" 2>/dev/null || {
    echo "  -> Installation des packages via pip..."
    pip install -r requirements.txt --quiet
}
echo "✓ Toutes les dépendances Python sont opérationnelles."

# 4. Exécution du générateur vidéo maître
echo ""
echo "🚀 Lancement de la génération vidéo complète..."
python3 generate_video_mynichepilot.py "$@"

echo ""
echo "======================================================================="
echo "🎉 Production terminée avec succès !"
echo "Retrouvez vos vidéos dans le dossier : $DIR/output"
echo "======================================================================="
