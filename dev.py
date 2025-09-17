import os
import sys
import socket
import subprocess
from pathlib import Path
import ipaddress


PROJECT_ROOT = Path(__file__).resolve().parent


def find_venv_python() -> Path | None:
    """
    Locate the virtual environment's Python executable.
    Search order:
    1) DEV_VENV env var (absolute or relative to project root)
    2) Common names in project root: venv, .venv, env
    3) Scan immediate subdirectories for a Scripts/python.exe
    """
    # 1) Explicit override via env var
    env_venv = os.environ.get("DEV_VENV")
    if env_venv:
        env_path = Path(env_venv)
        if not env_path.is_absolute():
            env_path = PROJECT_ROOT / env_path
        python_path = env_path / "Scripts" / "python.exe"
        if python_path.exists():
            return python_path

    # 2) Common names at root
    candidate_dirs = [
        PROJECT_ROOT / "venv",
        PROJECT_ROOT / ".venv",
        PROJECT_ROOT / "env",
    ]

    for candidate in candidate_dirs:
        python_path = candidate / "Scripts" / "python.exe"
        if python_path.exists():
            return python_path

    # Fallback: scan one level deep for a venv-like structure
    for child in PROJECT_ROOT.iterdir():
        if child.is_dir():
            python_path = child / "Scripts" / "python.exe"
            if python_path.exists():
                return python_path

    return None


def create_venv(target_dir: Path) -> Path | None:
    """Create a virtual environment at target_dir using the current Python.
    Returns the path to the created venv's python.exe or None on failure.
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Creating virtual environment at: {target_dir}")
        code = subprocess.call([sys.executable, "-m", "venv", str(target_dir)])
        if code != 0:
            print("Failed to create virtual environment", file=sys.stderr)
            return None
        python_path = target_dir / "Scripts" / "python.exe"
        if python_path.exists():
            # Best-effort: upgrade pip in the fresh venv
            try:
                subprocess.call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
            except Exception:
                pass
            return python_path
    except Exception as exc:
        print(f"Error creating venv: {exc}", file=sys.stderr)
    return None


def find_manage_py() -> Path | None:
    """
    Locate manage.py in the project.
    - Prefer at project root
    - Otherwise search up to a few levels deep, skipping common venv dirs
    """
    root_candidate = PROJECT_ROOT / "manage.py"
    if root_candidate.exists():
        return root_candidate

    skip_dirs = {"venv", ".venv", "env", "node_modules", ".git", ".idea", ".vscode"}
    max_depth = 3

    root_parts = len(PROJECT_ROOT.parts)
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        # Prune directories we don't want to descend into
        dirnames[:] = [d for d in dirnames if d.lower() not in skip_dirs]

        # Limit search depth
        depth = len(Path(dirpath).parts) - root_parts
        if depth > max_depth:
            dirnames[:] = []
            continue

        if "manage.py" in filenames:
            return Path(dirpath) / "manage.py"

    return None


def run(cmd: list[str], cwd: Path | None = None) -> int:
    process = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
    return process.returncode


def pip_install(python_exe: Path, args: list[str]) -> int:
    cmd = [str(python_exe), "-m", "pip", *args]
    return run(cmd)


def print_python_context(python_exe: Path) -> None:
    try:
        out = subprocess.check_output([
            str(python_exe),
            "-c",
            (
                "import sys,site,sysconfig;"
                "print('Python:', sys.executable);"
                "print('Prefix:', sys.prefix);"
                "print('Base Prefix:', sys.base_prefix);"
                "print('Site-packages:', sysconfig.get_paths().get('purelib'))"
            ),
        ])
        print(out.decode().strip())
    except Exception:
        pass


def ensure_dependencies(python_exe: Path, requirements_file: Path | None) -> None:
    """
    Install dependencies.
    - If requirements.txt exists, install from it.
    - Otherwise, ensure at least Django is installed.
    """
    requirements = requirements_file if requirements_file and requirements_file.exists() else PROJECT_ROOT / "requirements.txt"

    # Ensure pip itself is available and reasonably up to date (best-effort)
    try:
        pip_install(python_exe, ["--version"])  # probe
        pip_install(python_exe, ["install", "--upgrade", "pip"])  # best-effort
    except Exception:
        pass

    if requirements.exists():
        print(f"Installing dependencies from {requirements} ...")
        code = pip_install(python_exe, [
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "-r",
            str(requirements),
        ])
        if code != 0:
            print("Failed to install from requirements.txt", file=sys.stderr)
            sys.exit(code)
    else:
        # Minimal guarantee: Django present
        try:
            subprocess.check_call([str(python_exe), "-c", "import django; print(django.__version__)"])
            print("Django already installed.")
        except subprocess.CalledProcessError:
            print("Django not found. Installing django ...")
            code = pip_install(python_exe, [
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "django",
            ])
            if code != 0:
                print("Failed to install Django", file=sys.stderr)
                sys.exit(code)


def find_free_port(start_port: int = 8000, max_port: int = 8999) -> int:
    """Find a free TCP port by binding to 0.0.0.0 to catch conflicts across all interfaces."""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found in range 8000-8999")


def get_local_ip() -> str:
    """Best-effort to get a LAN IP for CSRF/hosts. Falls back to 127.0.0.1."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        # ensure it's a valid IPv4
        ipaddress.ip_address(ip)
        return ip
    except Exception:
        return "127.0.0.1"


def start_server(python_exe: Path, manage_py: Path, port: int) -> int:
    if not manage_py.exists():
        print("manage.py not found", file=sys.stderr)
        return 1

    address = f"0.0.0.0:{port}"
    print(f"Starting Django development server on {address} ...")
    cmd = [str(python_exe), str(manage_py), "runserver", address]
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    try:
        # Keep attached to the current console; stream stdout/stderr until interrupted
        return subprocess.call(cmd, cwd=manage_py.parent, env=env)
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\nServer stopped.")
        return 0


def main() -> None:
    print("Locating virtual environment ...")
    python_exe = find_venv_python()
    if not python_exe:
        # Decide where to create it: DEV_VENV or ./venv
        preferred = os.environ.get("DEV_VENV") or "venv"
        preferred_path = Path(preferred)
        if not preferred_path.is_absolute():
            preferred_path = PROJECT_ROOT / preferred_path
        python_exe = create_venv(preferred_path)
        if not python_exe:
            sys.exit(1)

    print(f"Using virtual env Python: {python_exe}")
    print("Interpreter context:")
    print_python_context(python_exe)

    manage_py = find_manage_py()
    if not manage_py:
        print("manage.py not found anywhere in the project", file=sys.stderr)
        sys.exit(1)

    # Prefer a requirements.txt adjacent to manage.py, then project root
    manage_requirements = manage_py.parent / "requirements.txt"

    print("Ensuring dependencies are installed ...")
    ensure_dependencies(python_exe, manage_requirements if manage_requirements.exists() else None)

    try:
        # Allow overriding the starting port via env var DEV_START_PORT
        env_start_port = os.environ.get("DEV_START_PORT")
        start_port = int(env_start_port) if env_start_port and env_start_port.isdigit() else 8000
        port = find_free_port(start_port, 8999)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Ensure DB is migrated so sessions/auth tables exist
    migrate_code = run([str(python_exe), str(manage_py), "migrate"], cwd=manage_py.parent)
    if migrate_code != 0:
        print("Migrations failed; cannot start server", file=sys.stderr)
        sys.exit(migrate_code)

    # Dynamically set dev-friendly env for hosts/CSRF so login sessions work reliably
    local_ip = get_local_ip()
    env = os.environ.copy()
    env.setdefault("DJANGO_DEBUG", "1")
    env.setdefault("DJANGO_ALLOWED_HOSTS", f"localhost,127.0.0.1,{local_ip}")
    # Include http scheme and chosen port for CSRF trusted origins
    env.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", f"http://localhost:{port},http://127.0.0.1:{port},http://{local_ip}:{port}")
    # Dev cookies over http
    env.setdefault("DJANGO_SESSION_COOKIE_SECURE", "0")
    env.setdefault("DJANGO_CSRF_COOKIE_SECURE", "0")

    # Re-run server with these env vars
    os.environ.update(env)

    code = start_server(python_exe, manage_py, port)
    sys.exit(code)


if __name__ == "__main__":
    main()


