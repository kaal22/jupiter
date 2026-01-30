#!/bin/bash
# Jupiter OS — All-in-one installer for Ubuntu Desktop
# Installs: system deps, Ollama, Ollama model (hardware-based), Jupiter package, systemd user services.
# Usage: curl -sSL https://raw.githubusercontent.com/kaal22/jupiter/main/install.sh | bash
#    or: cd /path/to/jupiter && ./install.sh
#    or: ./install.sh --clone https://github.com/kaal22/jupiter.git

set -e
JUPITER_REPO_URL="${JUPITER_REPO_URL:-https://github.com/kaal22/jupiter.git}"
CLONE_URL=""
while [ $# -gt 0 ]; do
  if [ "$1" = "--clone" ] && [ -n "${2:-}" ]; then
    CLONE_URL="$2"
    shift 2
  else
    shift
  fi
done

# When run via curl (no repo on disk), default to cloning from kaal22/jupiter
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if [ -z "$CLONE_URL" ] && [ ! -f "${SCRIPT_DIR}/pyproject.toml" ]; then
  CLONE_URL="$JUPITER_REPO_URL"
fi

# ─── Helpers ─────────────────────────────────────────────────────────────────
log() { echo "[Jupiter] $*"; }
warn() { echo "[Jupiter] WARNING: $*" >&2; }
die() { echo "[Jupiter] ERROR: $*" >&2; exit 1; }

# When cloning, we need git (and curl) before anything else
ensure_git() {
  if command -v git &>/dev/null; then
    return 0
  fi
  log "Installing git (required to clone Jupiter)..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq git ca-certificates curl --no-install-recommends
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y -q git ca-certificates curl
  elif command -v yum &>/dev/null; then
    sudo yum install -y -q git ca-certificates curl
  else
    die "git not found. Please install git and run again."
  fi
  # Ensure this shell sees git (PATH may be minimal when run via curl)
  export PATH="/usr/bin:/usr/local/bin:$PATH"
}

# ─── Config ─────────────────────────────────────────────────────────────────
if [ -n "$CLONE_URL" ]; then
  ensure_git
  GIT_CMD="$(command -v git 2>/dev/null || echo /usr/bin/git)"
  if [ ! -x "$GIT_CMD" ]; then
    die "git not found after install. Try: sudo apt-get install git && run again."
  fi
  CLONE_DIR="${TMPDIR:-/tmp}/jupiter-install-$$"
  log "Cloning Jupiter from $CLONE_URL into $CLONE_DIR..."
  "$GIT_CMD" clone --depth 1 "$CLONE_URL" "$CLONE_DIR"
  INSTALL_SRC="$CLONE_DIR"
  trap "rm -rf '$CLONE_DIR'" EXIT
else
  INSTALL_SRC="${JUPITER_INSTALL_SRC:-$SCRIPT_DIR}"
fi
JUPITER_INSTALL="${JUPITER_INSTALL:-$HOME/.local/share/jupiter-install}"
JUPITER_VENV="${JUPITER_VENV:-$HOME/.local/share/jupiter/venv}"
JUPITER_BIN="$HOME/.local/bin"
OLLAMA_INSTALL_URL="${OLLAMA_INSTALL_URL:-https://ollama.com/install.sh}"

# ─── Ubuntu / apt ───────────────────────────────────────────────────────────
check_ubuntu() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
      ubuntu|debian|linuxmint|pop) return 0 ;;
      *) warn "Not Ubuntu/Debian. Install may need manual steps." ;;
    esac
  fi
  return 0
}

install_apt_deps() {
  log "Installing system dependencies (apt)..."
  if ! command -v apt-get &>/dev/null; then
    warn "apt-get not found. Install Python 3.10+, python3-venv, curl manually."
    return 0
  fi
  sudo apt-get update -qq
  sudo apt-get install -y -qq \
    python3 \
    python3-venv \
    python3-pip \
    curl \
    ca-certificates \
    git \
    --no-install-recommends
  log "System dependencies installed."
}

# ─── Ollama ─────────────────────────────────────────────────────────────────
install_ollama() {
  if command -v ollama &>/dev/null; then
    log "Ollama already installed."
    return 0
  fi
  log "Installing Ollama..."
  curl -fsSL "$OLLAMA_INSTALL_URL" | sh
  log "Ollama installed."
}

start_ollama() {
  if systemctl --user is-active --quiet ollama 2>/dev/null; then
    log "Ollama (user) already running."
    return 0
  fi
  if systemctl is-active --quiet ollama 2>/dev/null; then
    log "Ollama (system) already running."
    return 0
  fi
  # Start Ollama in background so we can pull models (user service or direct)
  if systemctl --user list-unit-files --quiet ollama.service 2>/dev/null; then
    systemctl --user start ollama.service 2>/dev/null || true
  elif systemctl list-unit-files --quiet ollama.service 2>/dev/null; then
    sudo systemctl start ollama.service 2>/dev/null || true
  else
    (ollama serve &) 2>/dev/null || true
    sleep 3
  fi
  log "Ollama started."
}

# ─── Jupiter venv & package ──────────────────────────────────────────────────
install_jupiter_venv() {
  log "Creating Jupiter virtual environment at $JUPITER_VENV..."
  mkdir -p "$(dirname "$JUPITER_VENV")"
  python3 -m venv "$JUPITER_VENV"
  "$JUPITER_VENV/bin/pip" install --upgrade pip -q
  if [ -f "$INSTALL_SRC/requirements.txt" ]; then
    "$JUPITER_VENV/bin/pip" install -r "$INSTALL_SRC/requirements.txt" -q
  fi
  if [ -f "$INSTALL_SRC/pyproject.toml" ]; then
    "$JUPITER_VENV/bin/pip" install -e "$INSTALL_SRC" -q
  else
    die "No pyproject.toml in $INSTALL_SRC. Run install.sh from the Jupiter repo root."
  fi
  log "Jupiter Python package installed."
}

# ─── Hardware & model ───────────────────────────────────────────────────────
pull_ollama_model() {
  log "Detecting hardware and selecting model..."
  export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
  JUPITER_DATA="$XDG_DATA_HOME/jupiter"
  mkdir -p "$JUPITER_DATA"

  HARDWARE_JSON="$JUPITER_DATA/hardware.json"
  if [ -x "$INSTALL_SRC/provisioning/hardware_detect.py" ]; then
    (cd "$INSTALL_SRC" && python3 provisioning/hardware_detect.py) > "$HARDWARE_JSON" 2>/dev/null || true
  fi
  [ -s "$HARDWARE_JSON" ] || echo '{"gpu_vram_gb":0,"memory_mb":0}' > "$HARDWARE_JSON"

  MODEL_JSON="$JUPITER_DATA/model.json"
  if [ -x "$INSTALL_SRC/provisioning/model_policy.py" ]; then
    VRAM_GB=$(python3 -c "import json; print(json.load(open('$HARDWARE_JSON')).get('gpu_vram_gb',0))" 2>/dev/null || echo 0)
    (cd "$INSTALL_SRC" && python3 provisioning/model_policy.py "$VRAM_GB") > "$MODEL_JSON" 2>/dev/null || true
  fi
  [ -s "$MODEL_JSON" ] || echo '{"model":"llama3.2:3b"}' > "$MODEL_JSON"

  MODEL=$(python3 -c "import json; print(json.load(open('$MODEL_JSON')).get('model','llama3.2:3b'))" 2>/dev/null)
  log "Pulling Ollama model: $MODEL (this may take a few minutes)..."
  if command -v ollama &>/dev/null; then
    ollama pull "$MODEL" || warn "Ollama pull failed. You can run 'ollama pull llama3.2:3b' later."
  else
    warn "Ollama not in PATH. Pull a model later with: ollama pull llama3.2:3b"
  fi
  log "Model ready."
}

# ─── Copy install tree for first-boot ───────────────────────────────────────
copy_install_tree() {
  log "Copying Jupiter tree to $JUPITER_INSTALL (for first-boot and provisioning)..."
  mkdir -p "$(dirname "$JUPITER_INSTALL")"
  rsync -a --exclude='.venv' --exclude='.git' --exclude='__pycache__' --exclude='*.egg-info' \
    "$INSTALL_SRC/" "$JUPITER_INSTALL/" 2>/dev/null || {
    cp -a "$INSTALL_SRC" "$JUPITER_INSTALL"
    rm -rf "$JUPITER_INSTALL/.venv" "$JUPITER_INSTALL/.git" 2>/dev/null || true
  }
  chmod +x "$JUPITER_INSTALL/scripts/firstboot.sh" 2>/dev/null || true
  chmod +x "$JUPITER_INSTALL/provisioning/hardware_detect.py" "$JUPITER_INSTALL/provisioning/model_policy.py" 2>/dev/null || true
  log "Install tree copied."
}

# ─── Systemd user units ──────────────────────────────────────────────────────
install_systemd_units() {
  mkdir -p "$HOME/.config/systemd/user"
  for u in jupiter-firstboot.service jupiter-agent.service; do
    if [ -f "$INSTALL_SRC/systemd/$u" ]; then
      cp "$INSTALL_SRC/systemd/$u" "$HOME/.config/systemd/user/"
      log "Installed systemd user unit: $u"
    fi
  done
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user enable jupiter-firstboot.service 2>/dev/null || true
  systemctl --user enable jupiter-agent.service 2>/dev/null || true
  log "Systemd user services enabled (jupiter-firstboot, jupiter-agent)."
}

# ─── CLI in PATH ─────────────────────────────────────────────────────────────
add_local_bin_to_path() {
  local path_line="export PATH=\"\$HOME/.local/bin:\$PATH\""
  for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    [ -f "$rc" ] || continue
    if grep -q '.local/bin' "$rc" 2>/dev/null; then
      return 0
    fi
    echo "" >> "$rc"
    echo "# Jupiter CLI" >> "$rc"
    echo "$path_line" >> "$rc"
    log "Added ~/.local/bin to PATH in $rc"
    return 0
  done
  # No rc file found, create .bashrc
  echo "$path_line" >> "$HOME/.bashrc"
  log "Created ~/.bashrc with ~/.local/bin in PATH"
}

install_cli_symlink() {
  mkdir -p "$JUPITER_BIN"
  if [ -f "$JUPITER_VENV/bin/jupiter" ]; then
    ln -sf "$JUPITER_VENV/bin/jupiter" "$JUPITER_BIN/jupiter"
    log "Installed 'jupiter' command at $JUPITER_BIN/jupiter"
  fi
  if ! echo "$PATH" | grep -q "$JUPITER_BIN"; then
    add_local_bin_to_path
    log "Run: source ~/.bashrc   (or open a new terminal) then try: jupiter chat"
  fi
}

# ─── DB init ─────────────────────────────────────────────────────────────────
init_jupiter_db() {
  log "Initializing Jupiter data and DB..."
  "$JUPITER_VENV/bin/python" -c "
from jupiter.config import ensure_dirs
from jupiter.storage.memory import MemoryStore
from jupiter.storage.audit import AuditStore
ensure_dirs()
MemoryStore()
AuditStore()
print('DB init ok')
" 2>/dev/null || true
  touch "$HOME/.local/share/jupiter/.provisioned" 2>/dev/null || true
  log "Jupiter data initialized."
}

# ─── Main ───────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "  Jupiter OS — All-in-one installer (Ubuntu Desktop)"
  echo "════════════════════════════════════════════════════════════"
  echo ""

  check_ubuntu
  install_apt_deps
  install_ollama
  start_ollama
  install_jupiter_venv
  copy_install_tree
  pull_ollama_model
  init_jupiter_db
  install_systemd_units
  install_cli_symlink

  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "  Jupiter OS installed successfully"
  echo "════════════════════════════════════════════════════════════"
  echo ""
  echo "  • Run once (or open a new terminal):  source ~/.bashrc"
  echo "  • Then:  jupiter chat   or  jupiter status"
  echo "  • Or use full path:  $JUPITER_VENV/bin/jupiter chat"
  echo ""
}

main "$@"
