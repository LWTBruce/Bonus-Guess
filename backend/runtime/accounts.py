import base64
import hashlib
import json
import secrets
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

from . import game_config


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


def _admin_flag(value):
    return value is True


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
        account["is_admin"] = _admin_flag(account.get("is_admin"))
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


def _safe_resolve(path):
    try:
        return path.resolve()
    except FileNotFoundError:
        return path.absolute()


def _read_json_file(path, default):
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return data if isinstance(data, dict) else default


def _write_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _merge_achievements_file(source, target):
    if not source.exists():
        return False
    source_data = _read_json_file(source, {"completed": {}})
    target_data = _read_json_file(target, {"completed": {}})
    merged = dict(source_data)
    merged.update(target_data)
    completed = {}
    source_completed = source_data.get("completed") if isinstance(source_data.get("completed"), dict) else {}
    target_completed = target_data.get("completed") if isinstance(target_data.get("completed"), dict) else {}
    completed.update(source_completed)
    completed.update(target_completed)
    merged["completed"] = completed
    _write_json_file(target, merged)
    source.unlink()
    return True


def _numeric_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _merge_rank_pass_entry(existing, incoming):
    if not existing:
        return incoming
    if not incoming:
        return existing
    if not isinstance(existing, dict) or not isinstance(incoming, dict):
        return existing
    merged = dict(existing)
    for key, value in incoming.items():
        merged.setdefault(key, value)
    existing_score = _numeric_or_none(existing.get("best_score"))
    incoming_score = _numeric_or_none(incoming.get("best_score"))
    if incoming_score is not None and (existing_score is None or incoming_score > existing_score):
        merged["best_score"] = incoming.get("best_score")
    for key in ("first_passed_at", "created_at"):
        values = [str(value) for value in (existing.get(key), incoming.get(key)) if value]
        if values:
            merged[key] = min(values)
    for key in ("latest_passed_at", "updated_at"):
        values = [str(value) for value in (existing.get(key), incoming.get(key)) if value]
        if values:
            merged[key] = max(values)
    return merged


def _merge_rank_progress_file(source, target):
    if not source.exists():
        return False
    source_data = _read_json_file(source, {"subjects": {}})
    target_data = _read_json_file(target, {"subjects": {}})
    merged = dict(target_data)
    subjects = {}
    source_subjects = source_data.get("subjects") if isinstance(source_data.get("subjects"), dict) else {}
    target_subjects = target_data.get("subjects") if isinstance(target_data.get("subjects"), dict) else {}
    for subject in set(source_subjects) | set(target_subjects):
        source_info = source_subjects.get(subject) if isinstance(source_subjects.get(subject), dict) else {}
        target_info = target_subjects.get(subject) if isinstance(target_subjects.get(subject), dict) else {}
        info = dict(source_info)
        info.update(target_info)
        try:
            source_highest = int(source_info.get("highest") or 0)
        except (TypeError, ValueError):
            source_highest = 0
        try:
            target_highest = int(target_info.get("highest") or 0)
        except (TypeError, ValueError):
            target_highest = 0
        info["highest"] = max(source_highest, target_highest)
        source_passed = source_info.get("passed") if isinstance(source_info.get("passed"), dict) else {}
        target_passed = target_info.get("passed") if isinstance(target_info.get("passed"), dict) else {}
        passed = dict(source_passed)
        for rank_id, entry in target_passed.items():
            passed[str(rank_id)] = _merge_rank_pass_entry(entry, passed.get(str(rank_id)))
        for rank_id, entry in source_passed.items():
            passed[str(rank_id)] = _merge_rank_pass_entry(passed.get(str(rank_id)), entry)
        info["passed"] = passed
        subjects[subject] = info
    merged["subjects"] = subjects
    _write_json_file(target, merged)
    source.unlink()
    return True


def _unique_target_path(target):
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for index in range(1, 1000):
        candidate = target.with_name(f"{stem}_legacy{index}{suffix}")
        if not candidate.exists():
            return candidate
    return target.with_name(f"{stem}_legacy_{uuid.uuid4().hex[:8]}{suffix}")


def _move_legacy_record_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            if source.read_bytes() == target.read_bytes():
                source.unlink()
                return target
        except OSError:
            pass
        target = _unique_target_path(target)
    shutil.move(str(source), str(target))
    return target


def _remove_empty_dirs(root):
    if not root.exists():
        return
    directories = sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True)
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass
    try:
        root.rmdir()
    except OSError:
        pass


def migrate_legacy_data(account_id):
    paths = account_paths(account_id)
    paths["record_dir"].mkdir(parents=True, exist_ok=True)
    paths["profile_dir"].mkdir(parents=True, exist_ok=True)
    stats = {"records_moved": 0, "state_files_merged": 0, "migrated_at": _now()}
    if LEGACY_RECORD_DIR.exists() and _safe_resolve(LEGACY_RECORD_DIR) != _safe_resolve(paths["record_dir"]):
        if _merge_achievements_file(LEGACY_RECORD_DIR / "achievements.json", paths["achievements_file"]):
            stats["state_files_merged"] += 1
        if _merge_rank_progress_file(LEGACY_RECORD_DIR / "rank_progress.json", paths["rank_progress_file"]):
            stats["state_files_merged"] += 1
        for source in sorted(LEGACY_RECORD_DIR.rglob("*")):
            if not source.is_file() or source.name in {"achievements.json", "rank_progress.json"}:
                continue
            if "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(LEGACY_RECORD_DIR)
            _move_legacy_record_file(source, paths["record_dir"] / relative)
            stats["records_moved"] += 1
        _remove_empty_dirs(LEGACY_RECORD_DIR)
    _copy_file_if_missing(LEGACY_PROFILE_DIR / "player_settings.json", paths["player_settings_file"])
    _copy_file_if_missing(LEGACY_PROFILE_DIR / "daily_terms.json", paths["daily_terms_file"])
    marker = paths["profile_dir"] / "legacy_record_migration.json"
    if stats["records_moved"] or stats["state_files_merged"] or not marker.exists():
        _write_json_file(marker, stats)
    return stats


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
        "is_admin": _admin_flag(is_admin),
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
        if account.get("id") != "bruce" and not account.get("is_admin"):
            return active_account()
        if account.get("id") == "bruce" and not account.get("is_admin"):
            if not _verify_password("test001", account.get("password") or {}):
                return active_account()
            account["is_admin"] = True
            save_accounts(data)
        migrate_legacy_data(account_id)
        active = active_account()
        if not active:
            set_active_session(account_id)
            active = public_account(account)
        return active
    return active_account()


def public_account(account):
    if not account:
        return None
    return {
        "id": account.get("id", ""),
        "nickname": account.get("nickname", ""),
        "created_at": account.get("created_at", ""),
        "last_login_at": account.get("last_login_at", ""),
        "is_admin": _admin_flag(account.get("is_admin")),
    }


def is_admin_account(account):
    return _admin_flag((account or {}).get("is_admin"))


def set_account_admin(account_id, is_admin=True):
    account_id = str(account_id or "").strip()
    data = load_accounts()
    account = data.get("accounts", {}).get(account_id)
    if not account:
        raise AccountError("账号不存在。")
    account["is_admin"] = _admin_flag(is_admin)
    account["updated_at"] = _now()
    save_accounts(data)
    return public_account(account)


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

    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue
        is_runtime_module = module_name in {
            "player_profile",
            "records",
            "rank_system",
            "app",
            "backend.runtime.player_profile",
            "backend.runtime.records",
            "backend.runtime.rank_system",
            "backend.app",
        }
        is_app_module = module_name.startswith("backend.app_modules.")
        if not is_runtime_module and not is_app_module:
            continue
        if hasattr(module, "RECORD_DIR"):
            module.RECORD_DIR = paths["record_dir"]
        if hasattr(module, "ACHIEVEMENTS_FILE"):
            module.ACHIEVEMENTS_FILE = paths["achievements_file"]
        if hasattr(module, "RANK_PROGRESS_FILE"):
            module.RANK_PROGRESS_FILE = paths["rank_progress_file"]
        if hasattr(module, "PROFILE_DIR"):
            module.PROFILE_DIR = paths["profile_dir"]
        if hasattr(module, "PLAYER_SETTINGS_FILE"):
            module.PLAYER_SETTINGS_FILE = paths["player_settings_file"]
        if hasattr(module, "DAILY_TERMS_FILE"):
            module.DAILY_TERMS_FILE = paths["daily_terms_file"]
        if hasattr(module, "clear_record_caches"):
            module.clear_record_caches()
        elif hasattr(module, "_RECORD_ENTRIES_CACHE"):
            module._RECORD_ENTRIES_CACHE.update({"root": None, "entries": None})
        if hasattr(module, "_DAILY_TERMS_CACHE"):
            module._DAILY_TERMS_CACHE.update({"date": None, "mtime_ns": None, "state": None})

    return paths
