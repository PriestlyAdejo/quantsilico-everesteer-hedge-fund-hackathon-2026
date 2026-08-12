"""Read-only host hardware probe (GPU / CPU / OS).

Shared by ``qseh doctor`` and ``/api/compute``. Numeric zeros stay numeric
zeros — never coerced to null when the sensor genuinely reports idle.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HardwareProbe:
    """Structured host hardware snapshot."""

    os_label: str
    os_raw: str
    cpu_model: str | None
    gpu_name: str | None
    gpu_vram_used_gb: float | None
    gpu_vram_total_gb: float | None
    gpu_util_pct: float | None
    gpu_driver: str | None
    cuda: str | None
    gpu_available: bool

    def doctor_gpu_line(self) -> str:
        """Compact one-line GPU summary for ``qseh doctor``."""
        if not self.gpu_available or not self.gpu_name:
            return "unavailable"
        bits = [self.gpu_name]
        if self.gpu_vram_total_gb is not None:
            bits.append(f"{self.gpu_vram_total_gb:g} GiB")
        if self.gpu_driver:
            bits.append(f"driver {self.gpu_driver}")
        return ", ".join(bits)


def probe_hardware() -> HardwareProbe:
    """Probe local OS, CPU, and NVIDIA GPU (best-effort, never raises)."""
    os_raw = platform.platform()
    return HardwareProbe(
        os_label=_humanise_os(os_raw),
        os_raw=os_raw,
        cpu_model=_cpu_friendly_name(),
        **_gpu_fields(),
    )


def _humanise_os(raw: str) -> str:
    system = platform.system()
    if system == "Windows":
        release = platform.release() or "?"
        build = ""
        # platform.version() often looks like '10.0.22631'
        version = platform.version() or ""
        match = re.search(r"(\d+\.\d+\.\d+)", version)
        if match:
            build = match.group(1).rsplit(".", 1)[-1]
        elif "Build" in raw:
            m2 = re.search(r"Build[.\s]?(\d+)", raw, re.IGNORECASE)
            if m2:
                build = m2.group(1)
        # Windows 10.0.22xxx is commonly Windows 11 for builds >= 22000
        try:
            build_n = int(build) if build else 0
        except ValueError:
            build_n = 0
        win_label = "Windows 11" if build_n >= 22000 else f"Windows {release}"
        if build:
            return f"{win_label} · build {build}"
        return win_label
    if system == "Linux":
        return f"Linux · {platform.release()}"
    if system == "Darwin":
        return f"macOS · {platform.mac_ver()[0] or platform.release()}"
    return raw


def _cpu_friendly_name() -> str | None:
    if sys.platform.startswith("win"):
        name = _windows_cpu_name()
        if name:
            return name
    # Linux: try /proc/cpuinfo
    if sys.platform.startswith("linux"):
        try:
            text = open("/proc/cpuinfo", encoding="utf-8", errors="replace").read()
            for line in text.splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip() or None
        except OSError:
            pass
    proc = (platform.processor() or "").strip()
    return proc or None


def _windows_cpu_name() -> str | None:
    """Read CPU name via CIM without loading Activate.ps1."""
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return None
    try:
        out = subprocess.run(  # noqa: S603
            [
                ps,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if out.returncode == 0:
            name = (out.stdout or "").strip()
            return name or None
    except (OSError, subprocess.TimeoutExpired):
        return None
    return None


def _gpu_fields() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "gpu_name": None,
        "gpu_vram_used_gb": None,
        "gpu_vram_total_gb": None,
        "gpu_util_pct": None,
        "gpu_driver": None,
        "cuda": None,
        "gpu_available": False,
    }
    smi = shutil.which("nvidia-smi")
    if not smi:
        empty["cuda"] = _cuda_summary(driver=None, smi_present=False)
        return empty

    query = (
        "name,memory.total,memory.used,utilization.gpu,driver_version"
    )
    try:
        out = subprocess.run(  # noqa: S603
            [
                smi,
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        empty["cuda"] = _cuda_summary(driver=None, smi_present=True)
        return empty

    if out.returncode != 0 or not (out.stdout or "").strip():
        empty["cuda"] = _cuda_summary(driver=None, smi_present=True)
        return empty

    line = out.stdout.strip().splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 5:
        empty["cuda"] = _cuda_summary(driver=None, smi_present=True)
        return empty

    name = parts[0] or None
    vram_total = _parse_float(parts[1])
    vram_used = _parse_float(parts[2])
    util = _parse_float(parts[3])
    driver = parts[4] or None

    # Convert MiB → GiB; keep exact 0.0 when idle
    vram_total_gb = None if vram_total is None else round(vram_total / 1024.0, 2)
    vram_used_gb = None if vram_used is None else round(vram_used / 1024.0, 2)

    return {
        "gpu_name": name,
        "gpu_vram_used_gb": vram_used_gb,
        "gpu_vram_total_gb": vram_total_gb,
        "gpu_util_pct": util,
        "gpu_driver": driver,
        "cuda": _cuda_summary(driver=driver, smi_present=True),
        "gpu_available": name is not None,
    }


def _parse_float(raw: str) -> float | None:
    text = (raw or "").strip()
    if not text or text.lower() in {"n/a", "[n/a]", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _cuda_summary(*, driver: str | None, smi_present: bool) -> str | None:
    bits: list[str] = []
    if driver:
        bits.append(f"Driver {driver}")
    nvcc = shutil.which("nvcc")
    toolkit = None
    if nvcc:
        try:
            out = subprocess.run(  # noqa: S603
                [nvcc, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            blob = (out.stdout or "") + (out.stderr or "")
            match = re.search(r"release\s+([\d.]+)", blob, re.IGNORECASE)
            if match:
                toolkit = match.group(1)
        except (OSError, subprocess.TimeoutExpired):
            toolkit = None
    if toolkit:
        bits.append(f"CUDA toolkit {toolkit}")
    elif smi_present:
        bits.append("native toolkit not detected")
    wsl = _wsl_nvidia_note()
    if wsl:
        bits.append(wsl)
    if not bits:
        return None
    return " · ".join(bits)


def _wsl_nvidia_note() -> str | None:
    """Mention WSL nvidia-smi only as a detail string, never as the primary GPU."""
    if not sys.platform.startswith("win"):
        return None
    wsl = shutil.which("wsl")
    if not wsl:
        return None
    try:
        out = subprocess.run(  # noqa: S603
            [wsl, "-e", "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0 and (out.stdout or "").strip():
            return "WSL nvidia-smi also available"
    except (OSError, subprocess.TimeoutExpired):
        return None
    return None
