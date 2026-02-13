"""
Sphere — мониторинг ресурсов (CPU, RAM) и оценка совместимости с ИИ.
"""

from typing import Tuple
import platform

try:
    import psutil
except ImportError:
    psutil = None


def get_cpu_percent() -> float:
    if psutil is None:
        return 0.0
    try:
        return psutil.cpu_percent(interval=None)
    except Exception:
        return 0.0


def get_memory_info() -> Tuple[float, float]:
    """Возвращает (used_gb, total_gb)."""
    if psutil is None:
        return 0.0, 0.0
    try:
        v = psutil.virtual_memory()
        return v.used / (1024 ** 3), v.total / (1024 ** 3)
    except Exception:
        return 0.0, 0.0


def get_system_info() -> dict:
    """Сбор информации о системе для теста совместимости с ИИ."""
    if psutil is None:
        return {"error": "Установите psutil: pip install psutil"}
    try:
        v = psutil.virtual_memory()
        system = platform.system()
        machine = platform.machine() or ""
        # Apple Silicon: macOS + arm64 (M1/M2/M3, включая Air/Pro/Max)
        is_apple_silicon = system == "Darwin" and "arm" in machine.lower()
        return {
            "cpu_count": psutil.cpu_count(logical=True) or 0,
            "ram_total_gb": round(v.total / (1024 ** 3), 1),
            "ram_available_gb": round(v.available / (1024 ** 3), 1),
            "disk_free_gb": round(psutil.disk_usage("/").free / (1024 ** 3), 1),
            "system": system,
            "machine": machine,
            "is_apple_silicon": is_apple_silicon,
        }
    except Exception as e:
        return {"error": str(e)}


def get_recommended_models(system_info: dict) -> list:
    """
    Рекомендации моделей Ollama по железу.
    Возвращает список строк вида "llama3.2:1b — лёгкая".
    """
    if "error" in system_info:
        return []
    ram_gb = system_info.get("ram_total_gb", 0)
    cpu_count = system_info.get("cpu_count", 0)
    is_apple = bool(system_info.get("is_apple_silicon"))

    # Ниже 4 ГБ RAM — честно предупреждаем, что комфортной работы не будет.
    if ram_gb < 4:
        return [
            "Устройство с <4 GB RAM — ИИ будет работать очень медленно.",
            "Рекомендуется минимум 4–6 GB RAM даже для самых маленьких моделей.",
        ]

    # 4–6 GB — только самые лёгкие модели.
    if ram_gb < 6:
        base = [
            "llama3.2:1b — очень лёгкая, подойдёт для слабых ПК / ноутбуков",
            "phi3:mini — компактная модель от Microsoft",
            "qwen2:0.5b — минимальные требования по памяти",
        ]
        if is_apple:
            base.append("На MacBook Air M1/M2 8 GB можно попробовать 3B‑модели, но с просадками скорости.")
        return base

    # 6–8 GB — уже можно 3B‑класс, но аккуратно.
    if ram_gb < 8:
        return [
            "llama3.2:1b — максимально отзывчивая",
            "llama3.2:3b — рабочий компромисс при 6–8 GB RAM",
            "phi3:medium — средний размер, но следите за нагрузкой",
        ]

    # 8–12 GB — комфортные 3B/7B.
    if ram_gb < 12:
        rec = [
            "llama3.2:3b — хороший баланс качества и скорости",
            "mistral:7b — качество при умеренной нагрузке (8–12 GB RAM)",
            "phi3:medium — универсальная модель",
        ]
        if is_apple:
            rec.append("MacBook Air/Pro M1/M2 8–16 GB: оптимальны модели до ~7B параметров.")
        return rec

    # 12–24 GB — 7–8B как основная рабочая лошадка.
    if ram_gb < 24:
        rec = [
            "llama3.1:8b — рекомендуемая по умолчанию для 16–24 GB RAM",
            "mistral:7b — быстрая и умная",
            "qwen2:7b — сильная универсальная модель",
            "deepseek-r1:7b — рассуждения и chain-of-thought",
        ]
        if is_apple:
            rec.append("Mac с 16–24 GB (M‑серия): можно стабильно использовать 7–8B модели.")
        return rec

    # 24–64 GB — можно думать о больших 30–70B, но с оглядкой на формат квантования.
    if ram_gb <= 64:
        rec = [
            "llama3.1:8b — быстрая и достаточная для большинства задач",
            "mistral:7b — рабочая лошадка",
            "qwen2:7b / 14b — больше качества при достаточном объёме RAM",
            "llama3.1:70b — возможна в квантованном виде, но требует аккуратной настройки (лучше 48–64 GB RAM)",
        ]
        if is_apple:
            rec.append("Mac Studio / MacBook Pro 32–64 GB: можно экспериментировать с 30–70B квантованными моделями.")
        return rec

    # >64 GB — хай‑энд стенд.
    return [
        "llama3.1:70b — максимальное качество (64+ GB RAM, лучше 80+)",
        "qwen2:72b — топ‑модель при большом объёме памяти",
        "llama3.1:8b и mistral:7b — быстрые модели для повседневной работы параллельно с тяжёлыми.",
    ]
