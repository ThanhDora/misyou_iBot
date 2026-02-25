import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
SCRIPTS_DIR = ROOT / "scripts"


def _get_dumper_path():
    system = platform.system().lower()
    if system == "darwin":
        candidates = [ROOT / "Il2CppDumper-mac", ROOT / "Il2CppDumper"]
    elif system == "linux":
        candidates = [ROOT / "Il2CppDumper", ROOT / "Il2CppDumper-linux"]
    else:
        candidates = [ROOT / "Il2CppDumper.exe", ROOT / "Il2CppDumper"]
    for p in candidates:
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    net6 = ROOT / "Il2CppDumper-net6" / "Il2CppDumper.dll"
    if net6.exists():
        return f"dotnet {net6}"
    return None


def run(executable_path: str, metadata_path: str, output_dir: str, copy_scripts: bool = True):
    exe = Path(executable_path).resolve()
    meta = Path(metadata_path).resolve()
    out = Path(output_dir).resolve()
    if not exe.exists():
        return False, f"Executable not found: {executable_path}"
    if not meta.exists():
        return False, f"Metadata not found: {metadata_path}"
    out.mkdir(parents=True, exist_ok=True)
    dumper = _get_dumper_path()
    if not dumper:
        return False, "Il2CppDumper binary not found. Add Il2CppDumper (macOS) or Il2CppDumper (Linux) to dumper/ folder."
    parts = dumper.split()
    if parts[0] == "dotnet":
        cmd = parts + [str(exe), str(meta), str(out)]
    else:
        cmd = [parts[0], str(exe), str(meta), str(out)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        log = f"{stdout}\n{stderr}".strip() if stderr else stdout
        if proc.returncode != 0:
            return False, log or f"Process exited with code {proc.returncode}"
        if copy_scripts and SCRIPTS_DIR.exists():
            for f in SCRIPTS_DIR.glob("*.py"):
                dest = out / f.name
                shutil.copy2(f, dest)
        return True, log
    except subprocess.TimeoutExpired:
        return False, "Dump timed out after 300s"
    except Exception as e:
        return False, str(e)


def run_from_args():
    if len(sys.argv) < 4:
        print("Usage: python run.py <executable> <global-metadata.dat> <output_dir>")
        sys.exit(1)
    ok, msg = run(sys.argv[1], sys.argv[2], sys.argv[3])
    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    run_from_args()
