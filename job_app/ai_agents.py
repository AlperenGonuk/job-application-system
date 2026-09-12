"""Desteklenen yapay zeka CLI ajanlarının kayıt defteri ve tespiti.

Uygulama tek bir araca bağlı değildir: PATH'te bulunan ajanlar otomatik tespit
edilir, kullanıcı Ayarlar'dan birini seçebilir veya kendi komutunu yazabilir.
Her profil yalnız "istemi gönder, düz metin yanıtı al" sözleşmesini tanımlar;
karar mantığı ve istem metinleri değişmez.
"""
from __future__ import annotations

import shlex
import shutil

# Otomatik seçimde denenme sırası
DETECTION_ORDER = ("hermes", "claude", "codex", "agy", "gemini", "pi", "cursor-agent")

# prompt_mode: "arg" istemi komut satırında, "stdin" ise standart girişten gönderir.
# model_args boşsa ajanın kendi varsayılan modeli kullanılır.
AGENT_PROFILES: dict[str, dict] = {
    "hermes": {
        "label": "Hermes",
        "executable": "hermes",
        "base_args": [],
        "provider_args": ["--provider", "{provider}"],
        "model_args": ["-m", "{model}"],
        "prompt_args": ["-z", "{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "anthropic",
        "default_models": {"fast": "claude-haiku-4-5-20251001", "deep": "claude-sonnet-4-6"},
        "install_hint": "pip install hermes-agent",
    },
    "claude": {
        "label": "Claude Code",
        "executable": "claude",
        "base_args": ["-p", "--output-format", "text"],
        "provider_args": [],
        "model_args": ["--model", "{model}"],
        "prompt_args": [],
        "prompt_mode": "stdin",
        "default_provider": "",
        "default_models": {"fast": "haiku", "deep": "sonnet"},
        "install_hint": "npm install -g @anthropic-ai/claude-code",
    },
    "codex": {
        "label": "Codex CLI",
        "executable": "codex",
        "base_args": ["exec"],
        "provider_args": [],
        "model_args": ["-m", "{model}"],
        "prompt_args": ["{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "",
        "default_models": {},
        "install_hint": "npm install -g @openai/codex",
    },
    "agy": {
        "label": "Antigravity (agy)",
        "executable": "agy",
        "base_args": ["--output-format", "text"],
        "provider_args": [],
        "model_args": ["--model", "{model}"],
        "prompt_args": ["-p", "{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "",
        "default_models": {},
        "install_hint": "https://antigravity.google",
    },
    "gemini": {
        "label": "Gemini CLI",
        "executable": "gemini",
        "base_args": [],
        "provider_args": [],
        "model_args": ["-m", "{model}"],
        "prompt_args": ["-p", "{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "",
        "default_models": {},
        "install_hint": "npm install -g @google/gemini-cli",
    },
    "pi": {
        "label": "Pi",
        "executable": "pi",
        "base_args": ["-p"],
        "provider_args": ["--provider", "{provider}"],
        "model_args": ["--model", "{model}"],
        "prompt_args": ["{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "",
        "default_models": {},
        "install_hint": "npm install -g @just-every/pi",
    },
    "cursor-agent": {
        "label": "Cursor Agent",
        "executable": "cursor-agent",
        "base_args": ["-p"],
        "provider_args": [],
        "model_args": ["--model", "{model}"],
        "prompt_args": ["{prompt}"],
        "prompt_mode": "arg",
        "default_provider": "",
        "default_models": {},
        "install_hint": "https://cursor.com/cli",
    },
}

CUSTOM_AGENT = "custom"
AUTO_AGENT = "auto"
# Windows komut satırı sınırı nedeniyle argümanla gönderilen istem için üst sınır.
MAX_ARGUMENT_PROMPT = 28000

# Ajan başına önerilen modeller. Bunlar YALNIZ öneridir: uygulama kendiliğinden
# göndermez, kullanıcı Ayarlar'dan uygularsa gönderilir. Model adları hızla
# değiştiği için burada yalnız doğrulanabilmiş adlar tutulur; listelenmeyen bir
# ajanda ajanın kendi varsayılan modeli kullanılır.
#
# fast  = ön eleme (çok sayıda kısa ilan kartı, ucuz ve hızlı model yeterli)
# deep  = detaylı eleme ve CV karşılaştırması (uzun ilan metni, güçlü model)
RECOMMENDED_MODELS: dict[str, dict[str, str]] = {
    "hermes": {"fast": "claude-haiku-4-5-20251001", "deep": "claude-sonnet-4-6"},
    "claude": {"fast": "haiku", "deep": "sonnet"},
    "codex": {"fast": "gpt-5.6-luna", "deep": "gpt-5.5"},
    "agy": {"fast": "gemini-3.8-flash-medium", "deep": "gemini-3.1-pro-high"},
}

# Ajanın kendi model listesini basan komut (varsa).
LIST_MODELS_COMMAND: dict[str, str] = {
    "hermes": "hermes model",
    "agy": "agy models",
    "pi": "pi --list-models",
}


def recommended_models(agent: str) -> dict[str, str]:
    """Ajan için önerilen fast/deep model adları; bilinmiyorsa boş sözlük."""
    return RECOMMENDED_MODELS.get(agent, {})


def list_models_command(agent: str) -> str:
    """Ajanın model listesini gösteren komut; yoksa boş dize."""
    return LIST_MODELS_COMMAND.get(agent, "")


def is_installed(agent: str) -> bool:
    """Ajanın çalıştırılabilir dosyası PATH'te mi?"""
    profile = AGENT_PROFILES.get(agent)
    return bool(profile) and shutil.which(profile["executable"]) is not None


def available_agents() -> list[str]:
    """PATH'te bulunan ajanları tespit sırasına göre döndürür."""
    return [agent for agent in DETECTION_ORDER if is_installed(agent)]


def custom_command(settings: dict) -> str:
    """Kullanıcının Ayarlar'da yazdığı özel komut şablonu."""
    value = settings.get("ai_custom_command", "")
    return value.strip() if isinstance(value, str) else ""


def resolve_agent(settings: dict) -> str | None:
    """Ayarlara göre kullanılacak ajanı belirler; hiçbiri yoksa None döndürür."""
    choice = settings.get("ai_agent", AUTO_AGENT)
    if choice == CUSTOM_AGENT:
        return CUSTOM_AGENT if custom_command(settings) else None
    if choice in AGENT_PROFILES:
        return choice if is_installed(choice) else None
    detected = available_agents()
    return detected[0] if detected else None


def agent_label(agent: str | None) -> str:
    """Arayüzde gösterilecek ad."""
    if agent == CUSTOM_AGENT:
        return "Özel komut"
    return AGENT_PROFILES.get(agent or "", {}).get("label", agent or "")


def model_for(agent: str, task: str, settings: dict) -> str:
    """Görev için model adı: önce kullanıcı ayarı, sonra profil varsayılanı."""
    override = settings.get(f"ai_model_{task}", "")
    if isinstance(override, str) and override.strip():
        return override.strip()
    return AGENT_PROFILES.get(agent, {}).get("default_models", {}).get(task, "")


def resolve_executable(name: str) -> str:
    """Çalıştırılabilir dosyanın tam yolunu döndürür.

    Windows'ta npm ile kurulan ajanlar uzantısız bir adla (``claude``) görünür
    ama gerçekte ``claude.cmd`` dosyasıdır; tam yol çözümlenmezse süreç
    başlatılamaz.
    """
    return shutil.which(name) or name


def _expand(template: list[str], values: dict[str, str]) -> list[str]:
    """Şablondaki yer tutucuları doldurur; değeri boşsa parçayı tamamen atar."""
    if not template:
        return []
    for placeholder, value in values.items():
        if f"{{{placeholder}}}" in "".join(template) and not value:
            return []
    return [part.format(**values) for part in template]


def build_command(agent: str, prompt: str, *, task: str, settings: dict) -> tuple[list[str], str | None]:
    """Çalıştırılacak komutu ve (varsa) standart girişten gönderilecek istemi üretir."""
    if agent == CUSTOM_AGENT:
        template = custom_command(settings)
        if not template:
            raise ValueError("Özel ajan komutu tanımlı değil.")
        parts = shlex.split(template, posix=False)
        parts[0] = resolve_executable(parts[0])
        if any("{prompt}" in part for part in parts):
            return [part.replace("{prompt}", prompt) for part in parts], None
        return parts, prompt

    profile = AGENT_PROFILES[agent]
    values = {
        "prompt": prompt,
        "model": model_for(agent, task, settings),
        "provider": settings.get("ai_provider", "") or profile.get("default_provider", ""),
    }
    command = [resolve_executable(profile["executable"])]
    command += _expand(profile.get("provider_args", []), values)
    command += _expand(profile.get("model_args", []), values)
    command += list(profile.get("base_args", []))
    if profile["prompt_mode"] == "stdin":
        return command, prompt
    command += _expand(profile.get("prompt_args", []), values)
    return command, None
