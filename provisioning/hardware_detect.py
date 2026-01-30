#!/usr/bin/env python3
"""Hardware detection for Jupiter: GPU VRAM, CPU, memory."""
import json
import platform
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def get_cpu_info():
    try:
        with open("/proc/cpuinfo") as f:
            lines = f.read().splitlines()
        model = next((l.split(":", 1)[1].strip() for l in lines if l.startswith("model name")), "Unknown")
        count = sum(1 for l in lines if l.startswith("processor"))
        return {"model": model, "cores": count}
    except Exception:
        return {"model": platform.processor() or "Unknown", "cores": 0}

def get_mem_info():
    try:
        with open("/proc/meminfo") as f:
            data = dict(line.split(None, 1) for line in f if ":" in line)
        total_kb = int((data.get("MemTotal") or "0").split()[0])
        avail_kb = int((data.get("MemAvailable") or "0").split()[0])
        return {"total_mb": total_kb // 1024, "avail_mb": avail_kb // 1024}
    except Exception:
        return {"total_mb": 0, "avail_mb": 0}

def get_gpu_vram_mb():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return int(r.stdout.strip().split("\n")[0].strip().split()[0])
    except (FileNotFoundError, ValueError, IndexError):
        pass
    try:
        r = subprocess.run(["rocm-smi", "--showmeminfo", "vram", "--json"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            for k, v in (d.get("card0", {}) or d).items():
                if "vram" in k.lower() and isinstance(v, (int, float)):
                    return int(v) // (1024 * 1024)
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        pass
    return 0

def main():
    cpu = get_cpu_info()
    mem = get_mem_info()
    vram_mb = get_gpu_vram_mb()
    out = {"cpu": cpu, "memory_mb": mem["total_mb"], "memory_avail_mb": mem["avail_mb"], "gpu_vram_mb": vram_mb, "gpu_vram_gb": vram_mb // 1024}
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
