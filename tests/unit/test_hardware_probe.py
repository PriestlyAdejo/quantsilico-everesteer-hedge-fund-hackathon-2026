"""Unit tests for shared hardware probe."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from qs_everesteer.hardware.probe import HardwareProbe, probe_hardware


def test_gpu_present_with_idle_zero() -> None:
    mock_out = MagicMock()
    mock_out.returncode = 0
    mock_out.stdout = "NVIDIA GeForce RTX 3070, 8192, 0, 0, 560.94\n"
    mock_out.stderr = ""

    with (
        patch("qs_everesteer.hardware.probe.shutil.which", side_effect=lambda n: n if n == "nvidia-smi" else None),
        patch("qs_everesteer.hardware.probe.subprocess.run", return_value=mock_out),
    ):
        hw = probe_hardware()

    assert hw.gpu_available is True
    assert hw.gpu_name == "NVIDIA GeForce RTX 3070"
    assert hw.gpu_vram_total_gb == 8.0
    assert hw.gpu_vram_used_gb == 0.0
    assert hw.gpu_util_pct == 0.0
    assert "560.94" in (hw.cuda or "")
    assert "unavailable" not in hw.doctor_gpu_line()


def test_gpu_unavailable_when_smi_missing() -> None:
    with patch("qs_everesteer.hardware.probe.shutil.which", return_value=None):
        hw = probe_hardware()
    assert hw.gpu_available is False
    assert hw.gpu_name is None
    assert hw.doctor_gpu_line() == "unavailable"


def test_gpu_malformed_csv() -> None:
    mock_out = MagicMock()
    mock_out.returncode = 0
    mock_out.stdout = "not-a-csv-line\n"
    mock_out.stderr = ""
    with (
        patch("qs_everesteer.hardware.probe.shutil.which", side_effect=lambda n: "nvidia-smi" if n == "nvidia-smi" else None),
        patch("qs_everesteer.hardware.probe.subprocess.run", return_value=mock_out),
    ):
        hw = probe_hardware()
    assert hw.gpu_available is False


def test_hardware_probe_dataclass_fields() -> None:
    hw = HardwareProbe(
        os_label="Windows 11 · build 22631",
        os_raw="raw",
        cpu_model="CPU",
        gpu_name=None,
        gpu_vram_used_gb=None,
        gpu_vram_total_gb=None,
        gpu_util_pct=None,
        gpu_driver=None,
        cuda=None,
        gpu_available=False,
    )
    assert hw.doctor_gpu_line() == "unavailable"
