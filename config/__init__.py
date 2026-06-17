"""Configuration package. Loads user API keys from root config.py when present."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_USER_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.py"


def _load_user_config_module():
    if not _USER_CONFIG_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_aign_user_config", _USER_CONFIG_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_user_config = _load_user_config_module()

if _user_config is not None:
    get_current_config = getattr(_user_config, "get_current_config", None)
else:
    get_current_config = None

__all__ = ["get_current_config"]
