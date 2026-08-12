"""Environment / event readiness checks."""

from __future__ import annotations

import platform
import shutil
import sys

from qs_everesteer.cli_app.common import console, print_kv, repo_root
from qs_everesteer.event.adapter import sdk_version
from qs_everesteer.hardware.probe import probe_hardware
from qs_everesteer.ops_status import write_ops_status
from qs_everesteer.paths import ensure_standard_dirs


def run_doctor() -> dict:
    root = repo_root()
    dirs = ensure_standard_dirs(root)
    disk = shutil.disk_usage(root)
    free_gb = disk.free / (1024**3)
    everest = sdk_version()
    hw = probe_hardware()
    result = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "os": hw.os_label,
        "cpu": hw.cpu_model,
        "everestapi": everest,
        "disk_free_gb": round(free_gb, 2),
        "gpu": hw.doctor_gpu_line(),
        "gpu_name": hw.gpu_name,
        "cuda": hw.cuda,
        "repo_root": str(root),
        "paths": {k: str(v) for k, v in dirs.items()},
        "ok": everest != "UNKNOWN" and free_gb > 0.5,
    }
    print_kv(
        [
            ("python", result["python"]),
            ("platform", result["platform"]),
            ("os", result["os"]),
            ("cpu", result["cpu"]),
            ("everestapi", result["everestapi"]),
            ("disk_free_gb", result["disk_free_gb"]),
            ("gpu", result["gpu"]),
            ("cuda", result["cuda"]),
            ("repo_root", result["repo_root"]),
            ("ok", result["ok"]),
        ],
        title="qseh doctor",
    )
    console.print(f"[dim]standard dirs ensured under[/dim] {root}")
    write_ops_status(
        "last_doctor.json",
        status="passing" if result["ok"] else "failing",
        detail=f"gpu={result['gpu']}; disk_free_gb={result['disk_free_gb']}",
        repo_root=root,
        extra={"ok": result["ok"], "gpu": result["gpu"]},
    )
    return result
