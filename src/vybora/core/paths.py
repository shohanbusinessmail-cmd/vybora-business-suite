"""Windows-safe application data paths.

Customer data lives OUTSIDE the install directory:
  Windows: %LOCALAPPDATA%/Vybora
  Linux/macOS (dev): $XDG_DATA_HOME/vybora or ~/.local/share/vybora
Override with VYBORA_DATA_DIR (used by tests).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data: Path
    logs: Path
    backups: Path
    license: Path
    attachments: Path

    @property
    def db_file(self) -> Path:
        return self.data / "vybora.db"

    def ensure(self) -> None:
        for p in (self.root, self.data, self.logs, self.backups, self.license, self.attachments):
            p.mkdir(parents=True, exist_ok=True)


def get_paths(app_name: str = "Vybora") -> AppPaths:
    override = os.environ.get("VYBORA_DATA_DIR")
    if override:
        root = Path(override)
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        root = Path(base) / app_name
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / app_name
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        root = Path(base) / app_name.lower()
    return AppPaths(
        root=root,
        data=root / "data",
        logs=root / "logs",
        backups=root / "backups",
        license=root / "license",
        attachments=root / "attachments",
    )
