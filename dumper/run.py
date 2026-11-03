import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
SCRIPTS_DIR = ROOT / "scripts"


NET6_DIR = ROOT / "Il2CppDumper-net6"


def _dotnet_cmd():
    dotnet = os.environ.get("DOTNET_PATH") or shutil.which("dotnet")
    return dotnet


def _get_dumper_cmd():
    """Return the command (list) that launches Il2CppDumper, or None.

    Linux (server/Docker) uses the official cross-platform build
    Il2CppDumper-net6 (https://github.com/Perfare/Il2CppDumper/releases),
    run through `dotnet`. IL2CPP_DUMPER_PATH can point to a custom binary or .dll.
    """
    custom = os.environ.get("IL2CPP_DUMPER_PATH")
    candidates = []
    if custom:
        candidates.append(Path(custom))
    system = platform.system().lower()
    if system == "darwin":
        candidates += [ROOT / "Il2CppDumper-mac", ROOT / "Il2CppDumper"]
    elif system == "windows":
        candidates += [ROOT / "Il2CppDumper.exe"]
    else:
        candidates += [ROOT / "Il2CppDumper"]
    candidates.append(NET6_DIR / "Il2CppDumper.dll")

    for p in candidates:
        if not p.exists():
            continue
        if p.suffix.lower() == ".dll":
            dotnet = _dotnet_cmd()
            if dotnet:
                return [dotnet, str(p)]
            continue
        if os.access(p, os.X_OK):
            return [str(p)]
    return None


def _ensure_config(cmd):
    """Il2CppDumper reads config.json next to its own binary; make sure ours
    (RequireAnyKey=false, so it never waits for a key press) is used."""
    target_dir = Path(cmd[-1]).parent
    target = target_dir / "config.json"
    if target_dir != ROOT and CONFIG_PATH.exists():
        try:
            if not target.exists() or target.read_bytes() != CONFIG_PATH.read_bytes():
                shutil.copy2(CONFIG_PATH, target)
        except OSError:
            pass


def run(executable_path: str, metadata_path: str, output_dir: str, copy_scripts: bool = True):
    exe = Path(executable_path).resolve()
    meta = Path(metadata_path).resolve()
    out = Path(output_dir).resolve()
    if not exe.exists():
        return False, f"Executable not found: {executable_path}"
    if not meta.exists():
        return False, f"Metadata not found: {metadata_path}"
    out.mkdir(parents=True, exist_ok=True)
    dumper = _get_dumper_cmd()
    if not dumper:
        return False, (
            "Il2CppDumper not found. On Linux install the .NET runtime and put "
            "Il2CppDumper-net6 in dumper/Il2CppDumper-net6/ (the Docker image does this), "
            "or set IL2CPP_DUMPER_PATH."
        )
    _ensure_config(dumper)
    cmd = dumper + [str(exe), str(meta), str(out)]
    env = os.environ.copy()
    # Il2CppDumper-net6 targets .NET 6; allow running on a newer runtime (8.0).
    env.setdefault("DOTNET_ROLL_FORWARD", "Major")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            env=env,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        log = f"{stdout}\n{stderr}".strip() if stderr else stdout
        if proc.returncode != 0:
            return False, log or f"Process exited with code {proc.returncode}"
        # Il2CppDumper exits 0 even on failure and prints "ERROR: ..." instead.
        if "ERROR:" in log:
            return False, log
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
