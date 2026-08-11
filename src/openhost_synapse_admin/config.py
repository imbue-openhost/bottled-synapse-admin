import os
from pathlib import Path

import attr


@attr.s(auto_attribs=True, frozen=True)
class Settings:
    static_dir: Path
    session_path: Path


def load_settings() -> Settings:
    """Read config from the environment. OPENHOST_APP_DATA_DIR is injected by the router when the manifest
    requests `app_data`; SYNAPSE_ADMIN_STATIC_DIR is set by our Dockerfile."""
    data_dir = Path(os.environ["OPENHOST_APP_DATA_DIR"])
    static_dir = Path(os.environ["SYNAPSE_ADMIN_STATIC_DIR"])
    if not static_dir.is_dir():
        raise RuntimeError(f"static dir does not exist: {static_dir}")
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(static_dir=static_dir, session_path=data_dir / "session.json")
