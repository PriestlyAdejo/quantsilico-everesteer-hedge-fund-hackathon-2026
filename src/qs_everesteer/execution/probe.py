"""Safe capability inventory; discovery never provisions or spends."""

from __future__ import annotations

import platform
import shutil
import subprocess
from importlib.util import find_spec

from qs_everesteer.execution.benchmark import latest_lane_passed
from qs_everesteer.execution.contracts import (
    BackendCapabilities,
    BackendLane,
    FundingSource,
)
from qs_everesteer.hardware.probe import probe_hardware


def probe_backends() -> list[BackendCapabilities]:
    """Return honest local evidence and UNKNOWN remote lanes.

    Authenticated remote operations require explicit provider probes elsewhere;
    package installation or a method name is not classified as availability.
    """
    hardware = probe_hardware()
    local_ops = ("submit", "status", "logs", "cancel", "artifact")
    native_gpu_verified = hardware.gpu_available and latest_lane_passed("LOCAL_NATIVE_GPU")
    cpu_frameworks = ["sklearn"]
    for module, label in (
        ("lightgbm", "lightgbm"),
        ("xgboost", "xgboost"),
        ("catboost", "catboost"),
        ("torch", "pytorch"),
    ):
        if find_spec(module) is not None:
            cpu_frameworks.append(label)
    capabilities = [
        BackendCapabilities(
            lane=BackendLane.LOCAL_CPU,
            available=True,
            verified_operations=local_ops,
            frameworks=tuple(cpu_frameworks),
            accelerator=hardware.cpu_model or "CPU",
            funding_source=FundingSource.INCLUDED_CREDIT,
            estimated_cost=0.0,
            reason="local subprocess execution verified",
        ),
        BackendCapabilities(
            lane=BackendLane.LOCAL_NATIVE_GPU,
            available=hardware.gpu_available,
            verified_operations=local_ops if native_gpu_verified else (),
            # The matched canary currently verifies XGBoost CUDA only. Installed
            # packages or visible hardware are not evidence for other frameworks.
            frameworks=("xgboost",) if native_gpu_verified else (),
            accelerator=hardware.gpu_name,
            vram_gb=hardware.gpu_vram_total_gb,
            funding_source=FundingSource.INCLUDED_CREDIT,
            estimated_cost=0.0,
            reason=(
                None
                if native_gpu_verified
                else "matched native-GPU canary has not passed"
                if hardware.gpu_available
                else "no usable native NVIDIA GPU detected"
            ),
        ),
    ]
    wsl_jax, wsl_reason = _probe_wsl_jax()
    capabilities.append(
        BackendCapabilities(
            lane=BackendLane.LOCAL_LINUX_JAX,
            available=wsl_jax,
            verified_operations=local_ops if wsl_jax else (),
            frameworks=("jax",) if wsl_jax else (),
            accelerator=hardware.gpu_name if wsl_jax else None,
            vram_gb=hardware.gpu_vram_total_gb if wsl_jax else None,
            funding_source=FundingSource.INCLUDED_CREDIT,
            estimated_cost=0.0,
            reason=None if wsl_jax else wsl_reason,
        )
    )
    for lane in (
        BackendLane.EVERESTEER_BUILTIN,
        BackendLane.EVERESTEER_CUSTOM_GPU,
        BackendLane.RUNPOD_GPU,
    ):
        capabilities.append(
            BackendCapabilities(
                lane=lane,
                available=False,
                verified_operations=(),
                funding_source=FundingSource.UNKNOWN,
                estimated_cost=None,
                reason="authenticated actionable capability probe has not been completed",
            )
        )
    return capabilities


def _probe_wsl_jax() -> tuple[bool, str | None]:
    """Verify JAX inside WSL itself; native-Windows imports are not evidence."""
    wsl = shutil.which("wsl") if platform.system() == "Windows" else None
    if not wsl:
        return False, "WSL is unavailable"
    try:
        result = subprocess.run(
            [
                wsl,
                "-e",
                "python3",
                "-c",
                "import jax; assert any(d.platform == 'gpu' for d in jax.devices())",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "WSL JAX probe timed out"
    except OSError as exc:
        return False, f"WSL JAX probe failed: {type(exc).__name__}"
    if result.returncode != 0:
        return False, "WSL JAX GPU runtime is not verified"
    return True, None
