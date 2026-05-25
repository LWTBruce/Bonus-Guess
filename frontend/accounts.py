import base64
import hashlib
import json
import secrets
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

import game_config


ROOT_PROFILE_DIR = game_config.PROJECT_DIR / "profile"
ACCOUNTS_FILE = ROOT_PROFILE_DIR / "accounts.json"
SESSION_FILE = ROOT_PROFILE_DIR / "session.json"
USERS_DIR = ROOT_PROFILE_DIR / "users"

LEGACY_RECORD_DIR = game_config.PROJECT_DIR / "record"
LEGACY_PROFILE_DIR = game_config.PROJECT_DIR / "profile"

PASSWORD_ITERATIONS = 180_000


class AccountError(ValueError):
    pass


def _now():
    return datetime.now().isoformat(timespec="seconds")


def normalize_nickname(nickname):
    text = str(nickname or "").strip()
    if not text:
        raise AccountError("请输入昵称。")
    if len(text) > 16:
        raise AccountError("昵称最多 16 个字符。")
    return text


def validate_password(password):
    text = str(password or "")
    if len(text) < 4:
        raise AccountError("密码至少 4 位。")
    if len(text) > 64:
        raise AccountError("密码最多 64 位。")
    return text


def nickname_key(nickname):
    return normalize_nickname(nickname).casefold()


def _hash_password(password, salt=None):
    password = validate_password(password)
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PASSWORD_ITERATIONS)
    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": PASSWORD_ITERATIONS,
        "salt": base64.b64encode(salt_bytes).decode("ascii"),
        "hash": base64.b64encode(digest).decode("ascii"),
    }


def _verify_password(password, password_data):
    try:
        salt = base64.b64decode(password_data.get("salt") or "")
        expected = base64.b64decode(password_data.get("hash") or "")
        iterations = int(password_data.get("iterations") or PASSWORD_ITERATIONS)
    except Exception:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", str(password or "").encode("utf-8"), salt, iterations)
    return secrets.compare_digest(digest, expected)


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return {"accounts": {}, "nickname_index": {}}
    try:
        data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"accounts": {}, "nickname_index": {}}
    if not isinstance(data.get("accounts"), dict):
        data["accounts"] = {}
    if not isinstance(data.get("nickname_index"), dict):
        data["nickname_index"] = {}
    rebuilt_index = {}
    for account_id, account in list(data["accounts"].items()):
        if not isinstance(account, dict):
            data["accounts"].pop(account_id, None)
            continue
        account.setdefault("id", account_id)
        try:
            key = nickname_key(account.get("nickname"))
        except AccountError:
            continue
        account["nickname_key"] = key
        rebuilt_index[key] = account_id
        account["is_admin"] = bool(account.get("is_admin"))
    data["nickname_index"].update(rebuilt_index)
    return data


def save_accounts(data):
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def account_paths(account_id):
    account_id = str(account_id or "").strip()
    root = USERS_DIR / account_id
    record_dir = root / "record"
    profile_dir = root / "profile"
    return {
        "root": root,
        "record_dir": record_dir,
        "profile_dir": profile_dir,
        "achievements_file": record_dir / "achievements.json",
        "rank_progress_file": record_dir / "rank_progress.json",
        "player_settings_file": profile_dir / "player_settings.json",
        "daily_terms_file": profile_dir / "daily_terms.json",
    }


def _copy_file_if_missing(source, target):
    if source.exists() and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def migrate_legacy_data(account_id):
    paths = account_paths(account_id)
    if LEGACY_RECORD_DIR.exists() and not paths["record_dir"].exists():
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        shutil.copytree(LEGACY_RECORD_DIR, paths["record_dir"], ignore=ignore)
    paths["profile_dir"].mkdir(parents=True, exist_ok=True)
    _copy_file_if_missing(LEGACY_PROFILE_DIR / "player_settings.json", paths["player_settings_file"])
    _copy_file_if_missing(LEGACY_PROFILE_DIR / "daily_terms.json", paths["daily_terms_file"])


def ensure_user_dirs(account_id):
    paths = account_paths(account_id)
    paths["record_dir"].mkdir(parents=True, exist_ok=True)
    paths["profile_dir"].mkdir(parents=True, exist_ok=True)
    return paths


def create_account(nickname, password, account_id=None, migrate_legacy=False, is_admin=False):
    nickname = normalize_nickname(nickname)
    password = validate_password(password)
    data = load_accounts()
    key = nickname_key(nickname)
    existing = data["nickname_index"].get(key)
    if existing:
        raise AccountError("这个昵称已经被注册。")
    account_id = str(account_id or uuid.uuid4().hex[:12]).strip()
    if account_id in data["accounts"]:
        raise AccountError("账号 ID 已存在。")
    account = {
        "id": account_id,
        "nickname": nickname,
        "nickname_key": key,
        "password": _hash_password(password),
        "created_at": _now(),
        "last_login_at": "",
        "is_admin": bool(is_admin),
    }
    data["accounts"][account_id] = account
    data["nickname_index"][key] = account_id
    save_accounts(data)
    if migrate_legacy:
        migrate_legacy_data(account_id)
    else:
        ensure_user_dirs(account_id)
    return public_account(account)


def ensure_local_bruce_account():
    data = load_accounts()
    key = "bruce"
    account_id = data.get("nickname_index", {}).get(key)
    if account_id and account_id in data.get("accounts", {}):
        account = data["accounts"][account_id]
        if not account.get("is_admin"):
            account["is_admin"] = True
            save_accounts(data)
        ensure_user_dirs(account_id)
        active = active_account()
        if not active:
            set_active_session(account_id)
            active = public_account(account)
        return active
    migrate_legacy = not bool(data.get("accounts"))
    account = create_account("Bruce", "test001", account_id="bruce", migrate_legacy=migrate_legacy, is_admin=True)
    active = active_account()
    if active:
        return active
    set_active_session(account["id"])
    return account


def public_account(account):
    if not account:
        return None
    return {
        "id": account.get("id", ""),
        "nickname": account.get("nickname", ""),
        "created_at": account.get("created_at", ""),
        "last_login_at": account.get("last_login_at", ""),
        "is_admin": bool(account.get("is_admin")),
    }


def is_admin_account(account):
    return bool((account or {}).get("is_admin"))


def list_public_accounts():
    accounts = [public_account(account) for account in load_accounts().get("accounts", {}).values()]
    accounts = [account for account in accounts if account]
    accounts.sort(key=lambda item: (item.get("created_at") or "", item.get("nickname") or ""))
    return accounts


def authenticate(nickname, password):
    data = load_accounts()
    account_id = data["nickname_index"].get(nickname_key(nickname))
    if not account_id:
        raise AccountError("昵称或密码不正确。")
    account = data["accounts"].get(account_id)
    if not account or not _verify_password(password, account.get("password") or {}):
        raise AccountError("昵称或密码不正确。")
    account["last_login_at"] = _now()
    save_accounts(data)
    ensure_user_dirs(account_id)
    set_active_session(account_id)
    return public_account(account)


def set_active_session(account_id):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps({"account_id": account_id, "updated_at": _now()}, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_active_session():
    try:
        SESSION_FILE.unlink()
    except FileNotFoundError:
        pass


def active_account():
    if not SESSION_FILE.exists():
        return None
    try:
        session = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    account_id = str(session.get("account_id") or "")
    account = load_accounts().get("accounts", {}).get(account_id)
    if not account:
        return None
    ensure_user_dirs(account_id)
    return public_account(account)


def change_password(account_id, old_password, new_password):
    data = load_accounts()
    account = data["accounts"].get(str(account_id or ""))
    if not account:
        raise AccountError("当前账号不存在。")
    if not _verify_password(old_password, account.get("password") or {}):
        raise AccountError("原密码不正确。")
    account["password"] = _hash_password(new_password)
    account["password_changed_at"] = _now()
    save_accounts(data)


def rename_account(account_id, new_nickname):
    new_nickname = normalize_nickname(new_nickname)
    data = load_accounts()
    account = data["accounts"].get(str(account_id or ""))
    if not account:
        raise AccountError("当前账号不存在。")
    old_key = account.get("nickname_key") or nickname_key(account.get("nickname"))
    new_key = nickname_key(new_nickname)
    existing = data["nickname_index"].get(new_key)
    if existing and existing != account_id:
        raise AccountError("这个昵称已经被注册。")
    if old_key != new_key:
        data["nickname_index"].pop(old_key, None)
        data["nickname_index"][new_key] = account_id
    account["nickname"] = new_nickname
    account["nickname_key"] = new_key
    account["updated_at"] = _now()
    save_accounts(data)
    return public_account(account)


def apply_account_context(account_id):
    paths = account_paths(account_id)
    ensure_user_dirs(account_id)

    game_config.RECORD_DIR = paths["record_dir"]
    game_config.ACHIEVEMENTS_FILE = paths["achievements_file"]
    game_config.RANK_PROGRESS_FILE = paths["rank_progress_file"]
    game_config.PROFILE_DIR = paths["profile_dir"]
    game_config.PLAYER_SETTINGS_FILE = paths["player_settings_file"]
    game_config.DAILY_TERMS_FILE = paths["daily_terms_file"]

    modules = {}
    for name in ("player_profile", "records", "rank_system", "app"):
        module = sys.modules.get(name)
        if module is not None:
            modules[name] = module

    player_profile = modules.get("player_profile")
    if player_profile is not None:
        player_profile.PROFILE_DIR = paths["profile_dir"]
        player_profile.PLAYER_SETTINGS_FILE = paths["player_settings_file"]

    records = modules.get("records")
    if records is not None:
        records.RECORD_DIR = paths["record_dir"]
        records.ACHIEVEMENTS_FILE = paths["achievements_file"]
        records.RANK_PROGRESS_FILE = paths["rank_progress_file"]
        records.DAILY_TERMS_FILE = paths["daily_terms_file"]

    rank_system = modules.get("rank_system")
    if rank_system is not None:
        rank_system.RANK_PROGRESS_FILE = paths["rank_progress_file"]

    app_module = modules.get("app")
    if app_module is not None:
        app_module.RECORD_DIR = paths["record_dir"]

    return paths
