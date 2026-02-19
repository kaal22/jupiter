#!/bin/bash
# Installation script for Jupiter V2 on Kali Linux (System-Native)

echo ">>> Resetting local changes to ensure clean update..."
git fetch origin
git reset --hard origin/main

echo ">>> Pulling latest V2 code..."
git pull

echo ">>> Installing dependencies via APT (safer)..."
sudo apt update
sudo apt install -y python3-prompt-toolkit python3-click python3-httpx python3-pip

echo ">>> Installing Jupiter System-Wide (Bypassing PEP 668)..."
# We use --break-system-packages because you requested NO VENV.
# This installs jupiter directly into /usr/local/bin or similar.
sudo pip3 install --break-system-packages .

echo ">>> Installation Complete!"
echo "Run 'jupiter shell' to start."
