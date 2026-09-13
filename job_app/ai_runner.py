"""Seçili yapay zeka ajanını güvenli parametrelerle çalıştıran bağdaştırıcı.

Ajanın global yapılandırmasını değiştirmez; her çağrıda komutu yeniden kurar.
İşlem kilidi ve zaman aşımı ile eşzamanlı çağrıları engeller. Standart çıktı
boşsa güvenli hata döndürür, oturum tahmin etmez.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import uuid

from job_app import ai_agents
from job_app.privacy import scrub_text
from job_app.process import hidden_process_options
from job_app.settings import load_settings
from job_app.storage import DATA_DIR

LOCK_FILE = DATA_DIR / ".ai-agent.lock"
LOCK_TIMEOUT = 300  # 5 dakika
DEFAULT_TIMEOUT = 180
_LOCK_TOKEN: str | None = None

# Desteklenen ajanların çoğu aslında kodlama ajanı: istem içinde bağlantı veya
# dosya adı görünce araç çağırmaya kalkarlar. Başsız (headless) çalışmada bu izin
# istekleri otomatik reddedilir ve ajan boş çıktı döndürür. Bu ön ek, görevin
# saf metin görevi olduğunu her ajana aynı biçimde söyler.
NO_TOOL_PREAMBLE = (
    "Bu bir metin görevidir. Hiçbir araç, komut, kabuk, dosya okuma/yazma veya web "
    "erişimi kullanma; hiçbir bağlantıyı açma. Yalnız aşağıda verilen metne bakarak "
    "yanıtla ve yalnız istenen çıktıyı yaz.\n\n"
)


class AgentError(Exception):
    """Yapay zeka bağdaştırıcı hatası."""


class AgentBusyError(AgentError):
    """Başka bir yapay zeka işlemi çalışıyor."""


def _acquire_lock() -> None:
    """Basit dosya tabanlı kilit. Zaman aşımı geçilmişse eski kilidi kaldırır."""
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
            stored = {}
            try:
                stored = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            lock_time = stored.get("timestamp", 0)
            if time.time() - lock_time > LOCK_TIMEOUT:
                try:
                    LOCK_FILE.unlink()
                    continue
                except FileNotFoundError:
                    continue
            pid = stored.get("pid", "?")
            raise AgentBusyError(
                f"Başka bir yapay zeka işlemi çalışıyor (PID: {pid}). "
                f"{LOCK_TIMEOUT}s sonra otomatik temizlenir."
            )
    raise AgentBusyError("Yapay zeka işlem kilidi alınamadı; lütfen tekrar deneyin.")


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


def run_agent(
    prompt: str,
    *,
    task: str = "fast",
    model_override: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    settings: dict | None = None,
) -> str:
    """Seçili ajanı çağırır ve düz metin yanıtını döndürür.

    - Ajanın global yapılandırmasını değiştirmez
    - Kişisel veri temizlenmiş istem gönderir
    - İşlem kilidi kullanır
    - Standart çıktı boşsa hatayla durur (oturum tahmini yapmaz)
    """
    settings = dict(settings if settings is not None else load_settings())
    if model_override:
        settings[f"ai_model_{task}"] = model_override

    agent = ai_agents.resolve_agent(settings)
    if not agent:
        raise AgentError(
            "Kullanılabilir bir yapay zeka ajanı bulunamadı. Ayarlar > Yapay zeka "
            "bölümünden bir ajan seçin veya kendi komutunuzu tanımlayın."
        )

    safe_prompt = NO_TOOL_PREAMBLE + scrub_text(prompt)
    try:
        command, stdin_text = ai_agents.build_command(agent, safe_prompt, task=task, settings=settings)
    except ValueError as error:  # CommandTransportError dahil: istem kırpılmaz, iş durur
        raise AgentError(str(error)) from error
    if stdin_text is None and len(safe_prompt) > ai_agents.MAX_ARGUMENT_PROMPT:
        raise AgentError(
            f"İstem bu ajan için fazla uzun ({len(safe_prompt)} karakter). "
            "Standart girişi destekleyen bir ajan seçin (örneğin Claude Code)."
        )

    _acquire_lock()
    try:
        result = subprocess.run(
            command,
            input=stdin_text,
            check=True,
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            **hidden_process_options(),
        )
        output = result.stdout.strip()
        if not output:
            detail = (result.stderr or "").strip()
            raise AgentError(
                f"'{ai_agents.agent_label(agent)}' boş yanıt döndürdü. Olası nedenler:\n"
                "- Model hesabı/API anahtarı ayarlanmamış\n"
                "- Ajan başsız çalışmada bir araç izni istedi ve otomatik reddedildi\n"
                "- Model yanıt vermedi\n"
                + (f"\nAjanın bildirdiği hata:\n{detail[:800]}\n" if detail else "")
                + "Güvenlik nedeniyle oturum deposundan tahmin yapılmıyor."
            )
        return output

    except FileNotFoundError:
        raise AgentError(
            f"'{command[0]}' komutu bulunamadı. Ajanın kurulu ve PATH'te olduğundan emin ol."
        )
    except subprocess.TimeoutExpired:
        raise AgentError(f"{ai_agents.agent_label(agent)} {timeout}s içinde yanıt vermedi.")
    except subprocess.CalledProcessError as exc:
        raise AgentError(
            f"{ai_agents.agent_label(agent)} hata kodu {exc.returncode}: "
            f"{exc.stderr or exc.stdout or '(çıktı yok)'}"
        )
    finally:
        _release_lock()
