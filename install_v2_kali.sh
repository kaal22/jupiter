#!/bin/bash
# Installation script for Jupiter V2 on Kali Linux (System-Native)

echo ">>> Resetting local changes to ensure clean update..."
git fetch origin
git reset --hard origin/main

echo ">>> Pulling latest V2 code..."
git pull

echo ">>> Installing dependencies via APT (safer)..."
sudo apt update
sudo apt install -y python3-prompt-toolkit python3-click python3-httpx python3-pip nmap curl

echo ">>> Checking for Ollama (AI Backend)..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed."
fi

echo ">>> ensuring Ollama service is running..."
sudo systemctl enable ollama
sudo systemctl start ollama

# Wait for service to be ready
echo "Waiting for Ollama API..."
sleep 5

echo ">>> Pulling default AI model (llama3.2:3b)..."
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "This may take a few minutes (approx 2GB download)..."
    ollama pull llama3.2:3b
else
    echo "Model llama3.2:3b already present."
fi

echo ">>> Force installing dependencies via PIP (to fix conflicts)..."
sudo pip3 install --break-system-packages prompt_toolkit click httpx

echo ">>> Installing Jupiter System-Wide (Bypassing PEP 668)..."
# We use --break-system-packages because you requested NO VENV.
# This installs jupiter directly into /usr/local/bin or similar.
sudo pip3 install --break-system-packages .

echo ">>> Installation Complete!"
echo "Run 'jupiter shell' to start."
