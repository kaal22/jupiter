#!/bin/bash
# Jupiter OS - Master Installer
# Installs Dependencies, AI Backend (Ollama), and Jupiter (via pipx)

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Jupiter OS Installer Starting...${NC}"

# 1. System Dependencies
echo -e "${YELLOW}>>> [1/4] Installing System Dependencies...${NC}"
sudo apt update
sudo apt install -y pipx python3-venv nmap curl build-essential python3-dev git
pipx ensurepath
# Source bashrc to ensure pipx is in path for this script? 
# Usually pipx puts binaries in ~/.local/bin. We'll add it to PATH temporarily.
export PATH=$PATH:~/.local/bin

# 2. AI Backend (Ollama)
echo -e "${YELLOW}>>> [2/4] Checking AI Backend (Ollama)...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "    Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}    Ollama is already installed.${NC}"
fi

# 3. Model Pull
echo -e "${YELLOW}>>> [3/4] Initializing AI Model (llama3.2:3b)...${NC}"
# Start service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "    Starting Ollama service..."
    sudo systemctl start ollama || (ollama serve &)
    sleep 5 # Wait for startup
fi

echo "    Pulling model... (This may verify existing images)"
ollama pull llama3.2:3b

# 4. Install Jupiter
echo -e "${YELLOW}>>> [4/4] Installing Jupiter OS...${NC}"
pipx install . --force

echo -e "${GREEN}>>> Installation Complete!${NC}"
echo -e "Run the dashboard:"
echo -e "    ${BLUE}jupiter dashboard${NC}"
echo -e "Run the CLI:"
echo -e "    ${BLUE}jupiter shell${NC}"
