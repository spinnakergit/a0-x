"""One-time setup script for the X.com Integration plugin.
Installs required Python dependencies.

Called by the Init button in Agent Zero's Plugin List UI.
Must define main() returning 0 on success, non-zero on failure."""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("x_init")


def _find_python():
    """Find the correct Python interpreter (prefer A0 venv)."""
    venv_python = Path("/opt/venv-a0/bin/python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _install(pip_name: str, python: str):
    """Install a package using uv (preferred) or pip as fallback."""
    uv = shutil.which("uv")
    if uv:
        subprocess.check_call([uv, "pip", "install", pip_name, "--python", python])
    else:
        subprocess.check_call([python, "-m", "pip", "install", pip_name])


def main():
    python = _find_python()
    # Map of import name -> pip package name
    deps = {
        "aiohttp": "aiohttp>=3.9,<4",
        "requests_oauthlib": "requests-oauthlib>=1.3,<2",
        "yaml": "pyyaml>=6.0",
    }
    failed = []
    for import_name, pip_name in deps.items():
        try:
            result = subprocess.run(
                [python, "-c", f"import {import_name}"],
                capture_output=True,
            )
            if result.returncode == 0:
                logger.info(f"{pip_name} already installed.")
                continue
        except Exception:
            pass
        logger.info(f"Installing {pip_name}...")
        try:
            _install(pip_name, python)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {pip_name}: {e}")
            failed.append(pip_name)

    if failed:
        logger.error(f"Failed to install: {', '.join(failed)}")
        return 1

    # Ensure symlink exists for plugin namespace imports
    plugin_dir = Path(__file__).resolve().parent
    for root in [Path("/a0"), Path("/git/agent-zero")]:
        plugins_dir = root / "plugins"
        if plugins_dir.is_dir():
            symlink = plugins_dir / "x"
            if not symlink.exists():
                try:
                    symlink.symlink_to(plugin_dir)
                    logger.info(f"Created symlink: {symlink} -> {plugin_dir}")
                except OSError as e:
                    logger.warning(f"Could not create symlink: {e}")
            break

    logger.info("All dependencies ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
