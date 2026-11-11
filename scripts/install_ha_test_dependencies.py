"""Install the conversation dependencies declared by the selected HA build."""

import json
from pathlib import Path
import subprocess
import sys

import homeassistant


def main() -> None:
    """Use the installed HA manifest, rather than stale copied version pins."""
    manifest_path = Path(next(iter(homeassistant.__path__))) / "components/conversation/manifest.json"
    requirements = json.loads(manifest_path.read_text())["requirements"]
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *requirements], check=True
    )


if __name__ == "__main__":
    main()
