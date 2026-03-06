from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any

from ldsrs2_launcher.domain.manifests import write_json


def write_software_metadata(path: Path, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    if extra:
        payload.update(extra)
    write_json(path, payload)
