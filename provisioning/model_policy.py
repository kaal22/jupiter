#!/usr/bin/env python3
"""Model selection from hardware (VRAM-based)."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jupiter.config import MODEL_POLICY, DEFAULT_MODEL

def select_model(gpu_vram_gb: int) -> str:
    bucket = 0
    for v in sorted(MODEL_POLICY.keys(), reverse=True):
        if gpu_vram_gb >= v:
            bucket = v
            break
    return MODEL_POLICY.get(bucket, DEFAULT_MODEL)

def main():
    if len(sys.argv) > 1:
        vram_gb = int(sys.argv[1])
    else:
        from provisioning.hardware_detect import get_gpu_vram_mb
        vram_gb = get_gpu_vram_mb() // 1024
    model = select_model(vram_gb)
    print(json.dumps({"model": model, "gpu_vram_gb": vram_gb}))

if __name__ == "__main__":
    main()
