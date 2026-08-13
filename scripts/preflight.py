"""Safe local preflight. Invoked by scripts/preflight.cmd. Never arms uploads."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QSEH = ROOT / ".venv" / "Scripts" / "qseh.exe"
PY = ROOT / ".venv" / "Scripts" / "python.exe"


def _pnpm_bin() -> str | None:
    return shutil.which("pnpm.cmd") or shutil.which("pnpm")


def _now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    out = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, out


def _dashboard_healthy() -> bool:
    code, out = _run([str(QSEH), "dashboard", "status"])
    if code != 0:
        return False
    lowered = out.lower()
    return "health" in lowered and ("pass" in lowered or "true" in lowered or '"ok"' in lowered)


def main() -> int:
    if not QSEH.is_file() or not PY.is_file():
        print("[qseh] Missing .venv — create it and pip install -e \".[dashboard,dev]\" first.")
        return 1

    env = os.environ.copy()
    env["QSEH_SYNTHETIC"] = "1"

    log_dir = ROOT / "artifacts" / "preflight"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"preflight-{_now_stamp()}.log"

    results: list[tuple[str, str]] = []
    critical_failed = False
    was_running = _dashboard_healthy()

    def record(label: str, status: str, output: str) -> None:
        results.append((label, status))
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n===== {label} ({status}) =====\n")
            fh.write(output)
            if not output.endswith("\n"):
                fh.write("\n")

    def run_step(label: str, cmd: list[str], *, cwd: Path | None = None, critical: bool = True) -> int:
        nonlocal critical_failed
        code, out = _run(cmd, cwd=cwd, env=env)
        status = "PASS" if code == 0 else "FAIL"
        record(label, status, f"$ {' '.join(cmd)}\n{out}")
        if code != 0 and critical:
            critical_failed = True
        return code

    # 1 doctor
    run_step("doctor", [str(QSEH), "doctor"])

    # 2 sdk info
    run_step("SDK inspection", [str(QSEH), "sdk", "info"])

    # 3 event inspect — disconnected is INFO
    code, out = _run([str(QSEH), "event", "inspect"], env=env)
    disconnected = any(
        token in out
        for token in (
            "DISCONNECTED",
            "NOT_CONNECTED",
            "UNAVAILABLE",
            "SYNTHETIC",
            "credential",
        )
    )
    if disconnected:
        record("Everesteer event not connected", "INFO", f"$ qseh event inspect\n{out}")
    elif code == 0:
        record("event inspect", "PASS", f"$ qseh event inspect\n{out}")
    else:
        record("event inspect", "FAIL", f"$ qseh event inspect\n{out}")
        critical_failed = True

    # 4-5 data
    run_step("synthetic dataset", [str(QSEH), "data", "pull", "--split", "train"])
    run_step("data audit", [str(QSEH), "data", "audit"])

    # 6 rehearsal
    run_step("rehearsal", [str(QSEH), "rehearsal"])

    # 7 pytest
    run_step(
        "Python tests",
        [str(PY), "-m", "pytest", "tests/unit", "tests/integration", "tests/contracts", "-q"],
    )

    # 8 docs build
    run_step("generated documentation", [str(QSEH), "docs", "build"])

    # 9 verify manifest
    code, out = _run(
        [str(PY), "-c", "from qs_everesteer.docs_build import verify_docs_manifest; print(verify_docs_manifest())"],
        env=env,
    )
    record("docs-manifest", "PASS" if code == 0 else "FAIL", out)
    if code != 0:
        critical_failed = True

    # 10 diagnose
    run_step("dashboard diagnostics", [str(QSEH), "dashboard", "diagnose"])

    # 11 lifecycle
    life_ok = True
    life_out = []
    code, out = _run([str(QSEH), "dashboard", "start"], env=env)
    life_out.append(out)
    if code != 0:
        life_ok = False
    else:
        code, out = _run(
            [str(PY), "-c", "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8766/api/health', timeout=8).read().decode())"],
            env=env,
        )
        life_out.append(out)
        if code != 0 or "ok" not in out.lower():
            life_ok = False
        code, out = _run(
            [str(PY), "-c", "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8766/api/docs', timeout=8); body=r.read().decode(); assert 'cli-reference' in body and 'generatedFromSha' in body or 'generated_from_sha' in body; print('docs ok', len(body))"],
            env=env,
        )
        life_out.append(out)
        if code != 0:
            life_ok = False
        _run([str(QSEH), "dashboard", "stop"], env=env)
    record("dashboard lifecycle", "PASS" if life_ok else "FAIL", "\n".join(life_out))
    if not life_ok:
        critical_failed = True

    if was_running:
        _run([str(QSEH), "dashboard", "start"], env=env)
    else:
        _run([str(QSEH), "dashboard", "stop"], env=env)

    # 12 tsc
    frontend = ROOT / "dashboard" / "frontend"
    pnpm = _pnpm_bin()
    if not (frontend / "node_modules").is_dir():
        record("TypeScript", "INFO", "skipped — dashboard/frontend/node_modules missing")
    elif not pnpm:
        record("TypeScript", "FAIL", "pnpm.cmd not found on PATH")
        critical_failed = True
    else:
        try:
            run_step("TypeScript", [pnpm, "exec", "tsc", "--noEmit"], cwd=frontend)
        except OSError as exc:
            record("TypeScript", "FAIL", f"{type(exc).__name__}: {exc}")
            critical_failed = True

    # Human summary
    label_map = {name: status for name, status in results}
    def line(key: str, display: str) -> str:
        status = label_map.get(key, "FAIL")
        return f"{status:4}  {display}"

    summary = [
        "",
        "============================================================",
        " QUANTSILICO // EVERESTEER 2026 PREFLIGHT",
        "============================================================",
        "",
        line("doctor", "doctor"),
        line("SDK inspection", "SDK inspection"),
        line("Everesteer event not connected", "Everesteer event not connected")
        if "Everesteer event not connected" in label_map
        else line("event inspect", "event inspect"),
        line("synthetic dataset", "synthetic dataset"),
        line("data audit", "data audit"),
        line("rehearsal", "rehearsal"),
        line("Python tests", "Python tests"),
        line("generated documentation", "generated documentation"),
        line("docs-manifest", "docs-manifest"),
        line("dashboard diagnostics", "dashboard diagnostics"),
        line("dashboard lifecycle", "dashboard lifecycle"),
        line("TypeScript", "TypeScript"),
        "",
        "RESULT: "
        + ("READY FOR EVENT CONNECTION" if not critical_failed else "NOT READY — see log"),
        "",
        "Live credentials: NOT YET AVAILABLE" if disconnected or "Everesteer event not connected" in label_map else "Live credentials: inspect recorded",
        "Submission mode: DRY_RUN",
        "Real uploads: NOT ARMED",
        "",
        f"Log:\n{log_path.relative_to(ROOT).as_posix()}",
        "============================================================",
        "",
    ]
    text = "\n".join(summary)
    print(text)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(text)
    return 1 if critical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
