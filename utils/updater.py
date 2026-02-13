"""
Sphere — Обновления через Git.

Проверка новых коммитов в remote, установка по согласию пользователя.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger

# Корень репозитория (родитель utils/)
REPO_ROOT = Path(__file__).resolve().parent.parent


def is_git_repo() -> bool:
    """Проверить, что проект в Git-репозитории."""
    return (REPO_ROOT / ".git").exists()


def get_current_commit() -> Optional[str]:
    """Получить хеш текущего коммита."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]
    except Exception as e:
        logger.debug(f"get_current_commit: {e}")
    return None


def fetch_remote() -> bool:
    """Получить изменения с remote (без merge)."""
    try:
        result = subprocess.run(
            ["git", "fetch", "origin"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"fetch_remote: {e}")
    return False


def check_for_updates() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Проверить наличие обновлений.

    Returns:
        (has_updates, current_commit, new_commit)
        Если нет обновлений или ошибка — (False, current, None).
    """
    if not is_git_repo():
        return False, get_current_commit(), None

    current = get_current_commit()
    if not fetch_remote():
        return False, current, None

    try:
        # Сколько коммитов впереди на origin/main или origin/master?
        for branch in ["main", "master"]:
            result = subprocess.run(
                ["git", "rev-list", "--count", f"HEAD..origin/{branch}"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                count = int(result.stdout.strip())
                if count > 0:
                    r2 = subprocess.run(
                        ["git", "rev-parse", f"origin/{branch}"],
                        cwd=REPO_ROOT,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    new_commit = r2.stdout.strip()[:8] if r2.returncode == 0 else None
                    return True, current, new_commit
    except (ValueError, Exception) as e:
        logger.debug(f"check_for_updates: {e}")

    return False, current, None


def apply_update() -> Tuple[bool, str]:
    """
    Применить обновление (git pull).

    Returns:
        (success, message)
    """
    if not is_git_repo():
        return False, "Проект не в Git-репозитории."

    try:
        result = subprocess.run(
            ["git", "pull", "origin"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or "Обновление применено."
        return False, result.stderr.strip() or result.stdout.strip() or "Ошибка git pull."
    except subprocess.TimeoutExpired:
        return False, "Таймаут при обновлении."
    except Exception as e:
        logger.error(f"apply_update: {e}")
        return False, str(e)


def restart_app():
    """Перезапустить приложение (для применения обновлений)."""
    import os
    python = sys.executable
    script = sys.argv[0]
    os.execv(python, [python, script] + sys.argv[1:])
