#!/bin/bash
echo ""
echo "======================================="
echo "  Form Assistant — Installation rapide"
echo "======================================="
echo ""

# 1. Compiler le helper vibration
echo "[1/3] Compilation du helper vibration..."
if swiftc vibrate.swift -o vibrate 2>/dev/null; then
    echo "  OK"
else
    echo "  ERREUR: Swift non trouve."
    echo "  Installe Xcode CLI Tools: xcode-select --install"
    echo "  Puis relance ./setup.sh"
    exit 1
fi

# 2. Installer pynput
echo "[2/3] Installation de pynput..."
pip3 install --user pynput 2>/dev/null || pip install --user pynput 2>/dev/null
echo "  OK"

# 3. Configurer la cle API
echo "[3/3] Configuration de la cle API..."
if [ -f .env ]; then
    echo "  .env existe deja"
else
    echo ""
    read -p "  Colle ta cle API Anthropic (sk-ant-...): " key
    echo "ANTHROPIC_API_KEY=$key" > .env
    echo "  Cle sauvegardee dans .env"
fi

echo ""
echo "======================================="
echo "  Installation terminee!"
echo ""
echo "  Pour lancer:"
echo "    python3 form_mac.py"
echo ""
echo "  Cmd+I  = analyser le formulaire"
echo "  Ctrl+C = quitter"
echo "======================================="
echo ""
echo "  NOTE: macOS va te demander d'autoriser"
echo "  Terminal dans Preferences > Confidentialite"
echo "  > Accessibilite (une seule fois)"
echo ""
