#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
form_mac.py - Form Assistant invisible pour macOS

Tourne en arriere-plan, zero fenetre.
  Cmd+B  -> screenshot + analyse + vibrations
  Ctrl+C -> quitter

Les vibrations indiquent la position de la bonne reponse :
  3 vibrations = la 3e reponse en partant du haut

Installation :
    pip3 install pynput
    swiftc vibrate.swift -o vibrate

Usage :
    python3 form_mac.py
"""

import os
import sys
import json
import time
import base64
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path

try:
    from pynput import keyboard as pynput_kb
except ImportError:
    print("[ERREUR] pip3 install pynput")
    sys.exit(1)


# ============================================================
#  CONFIG
# ============================================================

API_URL    = "https://api.anthropic.com/v1/messages"
MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 2048
SCREENSHOT = "/tmp/fa_screen.png"
VIBRATE_BIN = str(Path(__file__).parent / "vibrate")
PAUSE_BETWEEN_QUESTIONS = 1.5   # secondes entre chaque question


# ============================================================
#  CLE API
# ============================================================

def load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    for candidate in [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# ============================================================
#  SCREENSHOT (screencapture CLI, zero dependance)
# ============================================================

def take_screenshot() -> str:
    """Capture l'ecran en silence, retourne le base64 du PNG."""
    subprocess.run(["screencapture", "-x", SCREENSHOT], check=True)
    with open(SCREENSHOT, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ============================================================
#  CLAUDE API
# ============================================================

def call_claude(api_key: str, img_b64: str) -> list:
    """Envoie le screenshot a Claude, retourne la liste de reponses."""
    prompt = (
        "Analyse ce formulaire visible a l'ecran.\n"
        "Pour chaque question avec des choix de reponses, "
        "determine la bonne reponse et sa POSITION parmi les choix "
        "(de haut en bas, 1 = premier choix).\n\n"
        "JSON array brut uniquement :\n"
        '[{"question":"...","answer":"...","position":2,"total":4}]\n\n'
        "- position = numero du choix correct (1 = premier en haut)\n"
        "- total = nombre total de choix visibles pour cette question\n"
        "- Pour champ texte libre : position=-1, total=0, answer=le texte a saisir\n"
        "- Ignore les boutons Suivant/Soumettre/Envoyer\n"
        "- JSON brut, pas de ```"
    )

    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": img_b64}},
            {"type": "text", "text": prompt}
        ]}]
    }).encode("utf-8")

    max_retries = 4
    for attempt in range(max_retries):
        req = urllib.request.Request(
            API_URL, data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            text = data["content"][0]["text"].strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )
            return json.loads(text)
        except urllib.error.HTTPError as e:
            if e.code == 529 and attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [API] Surcharge, retry dans {wait}s...")
                time.sleep(wait)
            else:
                raise


# ============================================================
#  VIBRATIONS
# ============================================================

def vibrate(n: int):
    """Vibre n fois via le helper Swift."""
    if n <= 0:
        return
    try:
        subprocess.run([VIBRATE_BIN, str(n)], check=True, timeout=10)
    except FileNotFoundError:
        print(f"  [!] Binaire vibrate introuvable: {VIBRATE_BIN}")
        print(f"      Compile-le: swiftc vibrate.swift -o vibrate")
    except Exception as e:
        print(f"  [!] Vibration echouee: {e}")


# ============================================================
#  PIPELINE D'ANALYSE
# ============================================================

_running = False

def analyze(api_key: str):
    global _running
    if _running:
        print("[!] Analyse deja en cours...")
        return
    _running = True

    def _run():
        global _running
        try:
            print("\n" + "=" * 40)
            print("[1/3] Screenshot...")
            img_b64 = take_screenshot()
            print(f"  OK ({len(img_b64) // 1024} Ko)")

            print("[2/3] Analyse par Claude...")
            answers = call_claude(api_key, img_b64)
            print(f"  {len(answers)} question(s) trouvee(s)\n")

            print("[3/3] Vibrations :")
            for i, a in enumerate(answers):
                q = a.get("question", "?")[:60]
                ans = a.get("answer", "?")
                pos = a.get("position", 0)
                total = a.get("total", 0)

                if pos > 0:
                    print(f"  Q{i+1}: {q}")
                    print(f"       -> {ans}  (choix {pos}/{total})")
                    print(f"       ** {pos} vibration(s) **")
                    vibrate(pos)
                else:
                    # Champ texte libre
                    print(f"  Q{i+1}: {q}")
                    print(f"       -> Texte: {ans}")
                    vibrate(1)  # 1 vibration pour signaler

                if i < len(answers) - 1:
                    time.sleep(PAUSE_BETWEEN_QUESTIONS)

            print("\n  Termine.")
            print("=" * 40)

        except json.JSONDecodeError as e:
            print(f"[ERREUR] JSON invalide: {e}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            print(f"[ERREUR] API HTTP {e.code}: {body}")
        except Exception as e:
            print(f"[ERREUR] {type(e).__name__}: {e}")
        finally:
            _running = False

    threading.Thread(target=_run, daemon=True).start()


# ============================================================
#  HOTKEY (Cmd+B)
# ============================================================

class HotkeyListener:
    def __init__(self, on_analyze):
        self._on_analyze = on_analyze
        self._cmd = False
        self._last = 0.0
        self._listener = None

    def start(self):
        self._listener = pynput_kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_press(self, key):
        if key in (pynput_kb.Key.cmd, pynput_kb.Key.cmd_r):
            self._cmd = True
            return

        if not self._cmd:
            return

        char = getattr(key, "char", None)
        if char == "b" or char == "\x02":
            now = time.time()
            if now - self._last > 1.5:
                self._last = now
                self._on_analyze()

    def _on_release(self, key):
        if key in (pynput_kb.Key.cmd, pynput_kb.Key.cmd_r):
            self._cmd = False


# ============================================================
#  MAIN
# ============================================================

def main():
    api_key = load_api_key()
    if not api_key:
        print("[ERREUR] Cle API introuvable.")
        print("  Option 1: ANTHROPIC_API_KEY=sk-ant-xxx python3 form_mac.py")
        print("  Option 2: Creer un fichier .env avec ANTHROPIC_API_KEY=sk-ant-xxx")
        sys.exit(1)

    # Verifier que le binaire vibrate existe
    if not os.path.isfile(VIBRATE_BIN):
        print(f"[!] Binaire vibrate introuvable: {VIBRATE_BIN}")
        print("    Compile-le avec: swiftc vibrate.swift -o vibrate")
        print("    (les vibrations ne fonctionneront pas sans)")
        print()

    print()
    print("=" * 44)
    print("  Form Assistant (macOS) — mode invisible")
    print(f"  Cle: ...{api_key[-8:]}")
    print()
    print("  Cmd+B   -> Analyser le formulaire")
    print("  Ctrl+C  -> Quitter")
    print("=" * 44)
    print()
    print("  Ouvre un formulaire dans ton navigateur")
    print("  puis appuie sur Cmd+B")
    print()

    hotkeys = HotkeyListener(on_analyze=lambda: analyze(api_key))
    hotkeys.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        hotkeys.stop()
        print("\n[Ferme]")


if __name__ == "__main__":
    main()
