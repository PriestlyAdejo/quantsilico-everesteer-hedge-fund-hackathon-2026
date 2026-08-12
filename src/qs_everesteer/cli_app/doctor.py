"""Environment / event readiness checks."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from qs_everesteer.cli_app.common import console, print_kv, repo_root
from qs_everesteer.event.adapter import sdk_version
from qs_everesteer.paths import ensure_standard_dirs


def _gpu_probe() -> str:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        pass
    return "unavailable"


def run_doctor() -> dict:
    root = repo_root()
    dirs = ensure_standard_dirs(root)
    disk = shutil.disk_usage(root)
    free_gb = disk.free / (1024**3)
    everest = sdk_version()
    result = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "everestapi": everest,
        "disk_free_gb": round(free_gb, 2),
        "gpu": _gpu_probe(),
        "repo_root": str(root),
        "paths": {k: str(v) for k, v in dirs.items()},
        "ok": everest != "UNKNOWN" and free_gb > 0.5,
    }
    print_kv(
        [
            ("python", result["python"]),
            ("platform", result["platform"]),
            ("everestapi", result["everestapi"]),
            ("disk_free_gb", result["disk_free_gb"]),
            ("gpu", result["gpu"]),
            ("repo_root", result["repo_root"]),
            ("ok", result["ok"]),
        ],
        title="qseh doctor",
    )
    console.print(f"[dim]standard dirs ensured under[/dim] {root}")
    return result
