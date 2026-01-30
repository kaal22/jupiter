#!/bin/bash
# Jupiter first-boot: hardware detect, DB init, model preference. Run once per user.
set -e
JUPITER_USER="${SUDO_USER:-$USER}"
JUPITER_HOME="${HOME:-/home/$JUPITER_USER}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$JUPITER_HOME/.local/share}"
JUPITER_DATA="$XDG_DATA_HOME/jupiter"
JUPITER_PROVISIONED="$JUPITER_DATA/.provisioned"
JUPITER_INSTALL="${JUPITER_INSTALL:-$XDG_DATA_HOME/jupiter-install}"

if [ -f "$JUPITER_PROVISIONED" ]; then
  exit 0
fi
mkdir -p "$JUPITER_DATA" "$JUPITER_HOME/.config/jupiter"

# Hardware snapshot
HARDWARE_JSON="$JUPITER_DATA/hardware.json"
if [ -x "$JUPITER_INSTALL/provisioning/hardware_detect.py" ]; then
  (cd "$JUPITER_INSTALL" && python3 provisioning/hardware_detect.py) > "$HARDWARE_JSON" 2>/dev/null || true
fi
[ -s "$HARDWARE_JSON" ] || echo '{"gpu_vram_gb":0,"memory_mb":0}' > "$HARDWARE_JSON"

# DB init via Python
VENV="$XDG_DATA_HOME/jupiter/venv"
if [ -f "$VENV/bin/python" ]; then
  "$VENV/bin/python" -c "
from jupiter.config import ensure_dirs
from jupiter.storage.memory import MemoryStore
from jupiter.storage.audit import AuditStore
ensure_dirs()
MemoryStore()
AuditStore()
print('DB init ok')
" 2>/dev/null || true
fi

# Model preference
if [ -x "$JUPITER_INSTALL/provisioning/model_policy.py" ]; then
  VRAM_GB=$(python3 -c "import json; print(json.load(open('$HARDWARE_JSON')).get('gpu_vram_gb',0))" 2>/dev/null || echo 0)
  (cd "$JUPITER_INSTALL" && python3 provisioning/model_policy.py "$VRAM_GB") > "$JUPITER_DATA/model.json" 2>/dev/null || true
fi

touch "$JUPITER_PROVISIONED"
if command -v systemctl >/dev/null 2>&1 && [ -n "$XDG_RUNTIME_DIR" ]; then
  systemctl --user disable jupiter-firstboot.service 2>/dev/null || true
fi
echo "Jupiter first-boot complete."
