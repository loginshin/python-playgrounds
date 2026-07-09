#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pip install -r macos/requirements-macos.txt
python3 -m PyInstaller \
  --windowed \
  --name LoGinKeyboard-macOS \
  --distpath releases/macos \
  --workpath build/LoGinKeyboard-macOS \
  --specpath build/LoGinKeyboard-macOS \
  --hidden-import pyperclip \
  --hidden-import Quartz \
  macos/login_keyboard_macos.py

echo "Built: releases/macos/LoGinKeyboard-macOS.app"
