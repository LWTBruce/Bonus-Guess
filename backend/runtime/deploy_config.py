import json
import os
from dataclasses import dataclass
from pathlib import Path


ENV_PREFIX = "BONUS_GUESS_"


@dataclass(frozen=True)
class WebRuntimeConfig:
    host: str
    port: int
    public_base_url: str
    resource_dir: Path
    data_dir: Path
    enable_online: bool


def _read_config_file(path):
    if not path:
        return {}
    target = Path(path).expanduser()
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enable", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disable", "disabled"}:
        return False
    return default


def _int_value(value, default):
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(1, min(65535, number))


def _path_value(value, default):
    if value in {None, ""}:
        return Path(default).expanduser().resolve()
    return Path(str(value)).expanduser().resolve()


def load_runtime_config(default_resource_dir, default_data_dir, config_path=None):
    config_file = config_path or os.environ.get(f"{ENV_PREFIX}WEB_CONFIG")
    file_data = _read_config_file(config_file)

    def value(name, default=None):
        env_value = os.environ.get(f"{ENV_PREFIX}{name.upper()}")
        if env_value is not None:
            return env_value
        return file_data.get(name, default)

    host = str(value("host", "127.0.0.1") or "127.0.0.1").strip() or "127.0.0.1"
    port = _int_value(value("port", 8765), 8765)
    public_base_url = str(value("public_base_url", "") or "").strip()
    resource_dir = _path_value(value("resource_dir"), default_resource_dir)
    data_dir = _path_value(value("data_dir"), default_data_dir)
    enable_online = _bool_value(value("enable_online"), False)
    return WebRuntimeConfig(
        host=host,
        port=port,
        public_base_url=public_base_url,
        resource_dir=resource_dir,
        data_dir=data_dir,
        enable_online=enable_online,
    )
