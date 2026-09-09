"""Güvenli Hermes CLI bağdaştırıcısı.

Hermes global config değiştirmez; her çağrıda --provider ve -m parametresi kullanır.
İşlem kilidi ve timeout ile eşzamanlı çağrıları engeller.
Stdout boşsa güvenli hata döndürür, oturum tahmin etmez.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from pii_temizle import scrub_text

ROOT = Path(__file__).resolve().parent
LOCK_FILE = ROOT / "data" / ".hermes.lock"
LOCK_TIMEOUT = 300  # 5 dakika
DEFAULT_TIMEOUT = 180
_LOCK_TOKEN: str | None = None


class HermesError(Exception):
    """Hermes bağdaştırıcı hatası."""


class HermesLockError(HermesError):
    """Başka bir Hermes işlemi çalışıyor."""


def _acquire_lock() -> None:
    """Basit dosya tabanlı kilit. Timeout aşılmışsa eski kilidi kaldırır."""
    global _LOCK_TOKEN
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    for _attempt in range(2):
        token = uuid.uuid4().hex
        try:
            descriptor = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump({"pid": os.getpid(), "timestamp": time.time(), "token": token}, file)
            _LOCK_TOKEN = token
            return
        except FileExistsError:
            load_lock = {}
            try:
                load_lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            lock_time = load_lock.get("timestamp", 0)
            if time.time() - lock_time > LOCK_TIMEOUT:
                try:
                    LOCK_FILE.unlink()
                    continue
                except FileNotFoundError:
                    continue
            pid = load_lock.get("pid", "?")
            raise HermesLockError(
                f"Başka bir Hermes işlemi çalışıyor (PID: {pid}). "
                f"{LOCK_TIMEOUT}s sonra otomatik temizlenir."
            )
    raise HermesLockError("Hermes işlem kilidi alınamadı; lütfen tekrar deneyin.")


def _release_lock() -> None:
    """Kilidi bırakır."""
    global _LOCK_TOKEN
    try:
        stored = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        if stored.get("token") == _LOCK_TOKEN:
            LOCK_FILE.unlink(missing_ok=True)
    except (OSError, json.JSONDecodeError):
        pass
    _LOCK_TOKEN = None


def hermes_run(
    prompt: str,
    *,
    provider: str = "anthropic",
    model_name: str = "claude-haiku-4-5-20251001",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Hermes CLI'yi güvenli parametrelerle çağırır.

    - Global config değiştirmez (--provider ve -m kullanır)
    - PII temizlenmiş prompt gönderir
    - İşlem kilidi kullanır
    - Stdout boşsa hatayla durur (oturum tahmini yapmaz)
    """
    # PII kontrolü
    safe_prompt = scrub_text(prompt)

    _acquire_lock()
    try:
        run_options = {
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "capture_output": True,
        }

        result = subprocess.run(
            ["hermes", "--provider", provider, "-m", model_name, "-z", safe_prompt],
            check=True,
            timeout=timeout,
            **run_options,
        )

        output = result.stdout.strip()
        if not output:
            raise HermesError(
                "Hermes stdout boş döndü. Olası nedenler:\n"
                "- Hermes CLI kurulu değil veya PATH'te değil\n"
                "- Model API anahtarı ayarlanmamış\n"
                "- Model yanıt vermedi\n"
                "Güvenlik nedeniyle oturum deposundan tahmin yapılmıyor."
            )

        return output

    except FileNotFoundError:
        raise HermesError(
            "'hermes' komutu bulunamadı. Hermes CLI'nin kurulu ve PATH'te olduğundan emin ol."
        )
    except subprocess.TimeoutExpired:
        raise HermesError(f"Hermes {timeout}s içinde yanıt vermedi.")
    except subprocess.CalledProcessError as exc:
        raise HermesError(f"Hermes hata kodu {exc.returncode}: {exc.stderr or exc.stdout or '(çıktı yok)'}")
    finally:
        _release_lock()
