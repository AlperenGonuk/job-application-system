"""Desteklenen yapay zeka CLI ajanlarının kayıt defteri ve tespiti.

Uygulama tek bir araca bağlı değildir: PATH'te bulunan ajanlar otomatik tespit
edilir, kullanıcı Ayarlar'dan birini seçebilir veya kendi komutunu yazabilir.
Her profil yalnız "istemi gönder, düz metin yanıtı al" sözleşmesini tanımlar;
karar mantığı ve istem metinleri değişmez.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
from pathlib import Path

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


class CommandTransportError(ValueError):
    """İstem, komut satırında kayıpsız ve güvenli biçimde taşınamıyor."""


# Windows'ta .cmd/.bat dosyaları her zaman cmd.exe üzerinden yorumlanır. cmd.exe
# argümanı satır sonunda keser (istemin yalnız ilk satırı gider) ve ", &, |, %,
# ^ gibi karakterleri komut olarak yorumlayabilir; ilan metni güvenilmeyen veri
# olduğu için bu bir komut enjeksiyonu yoludur. Bu yüzden yalnız bu güvenli
# kümeden oluşan argümanlar cmd.exe'ye bırakılır.
_BATCH_SUFFIXES = frozenset({".cmd", ".bat"})
_CMD_INTERPRETERS = frozenset({"cmd", "cmd.exe"})
# fullmatch ile kullanılır: "$" sondaki satır sonunu kabul ettiği için match yetmez.
_CMD_SAFE_ARGUMENT = re.compile(r"[A-Za-z0-9 _\-.:/\\=@+,]*")
# npm cmd-shim biçimi: "%dp0%\node_modules\paket\cli.js" %*  (eski: "%~dp0\...")
_SHIM_TARGET = re.compile(r'"%(?:~dp0|dp0%)\\(?P<target>[^"%\r\n]+)"\s*%\*', re.IGNORECASE)
_NODE_SCRIPT_SUFFIXES = frozenset({".js", ".mjs", ".cjs"})


def _runs_through_cmd(executable: str) -> bool:
    if os.name != "nt":
        return False
    path = Path(executable)
    return path.suffix.lower() in _BATCH_SUFFIXES or path.name.lower() in _CMD_INTERPRETERS


def resolve_batch_shim(shim: Path) -> list[str] | None:
    """npm'in ürettiği .cmd kısayolunun çağırdığı gerçek programı bulur.

    Yalnız tek hedefli standart cmd-shim biçimi tanınır. Hedef bir Node betiğiyse
    ``[node, betik]``, doğrudan bir .exe ise ``[exe]`` döner. Tanınmayan her
    durumda None döner; tahmin yapılmaz.
    """
    try:
        content = shim.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    targets = {match.group("target").strip() for match in _SHIM_TARGET.finditer(content)}
    if len(targets) != 1:
        return None
    target = Path(os.path.normpath(shim.parent / targets.pop()))
    if not target.is_file():
        return None
    suffix = target.suffix.lower()
    if suffix == ".exe":
        return [str(target)]
    if suffix in _NODE_SCRIPT_SUFFIXES:
        bundled = shim.parent / "node.exe"
        node = str(bundled) if bundled.is_file() else shutil.which("node")
        return [node, str(target)] if node else None
    return None


def safe_command(command: list[str]) -> list[str]:
    """Komutu, argümanları cmd.exe yorumlamasına maruz kalmayacak biçime getirir.

    - cmd.exe'den geçmeyen komutlar olduğu gibi döner (argümanlar doğrudan
      CreateProcess/exec ile, kabuk olmadan iletilir).
    - .cmd/.bat komutunun tüm argümanları güvenli kümedeyse olduğu gibi döner.
    - Aksi halde npm kısayolu çözülür ve alttaki program kabuksuz çağrılır.
    - Çözülemezse istem kırpılmak yerine açık bir hatayla durulur.
    """
    if not command or not _runs_through_cmd(command[0]):
        return command
    arguments = command[1:]
    if all(_CMD_SAFE_ARGUMENT.fullmatch(argument) for argument in arguments):
        return command
    if Path(command[0]).suffix.lower() in _BATCH_SUFFIXES:
        target = resolve_batch_shim(Path(command[0]))
        if target:
            return [*target, *arguments]
    raise CommandTransportError(
        f"'{Path(command[0]).name}' bir Windows toplu iş dosyası (cmd.exe üzerinden çalışır). "
        "İstem çok satırlı metin ve özel karakterler içerdiği için bu yoldan kayıpsız ve "
        "güvenli gönderilemez. Standart girişi kullanan bir ajan seçin, özel komuttan "
        "{prompt} yer tutucusunu kaldırın (istem standart girişten gider) veya komutta "
        "doğrudan gerçek programı (.exe ya da node betik.js) belirtin."
    )


def _expand(template: list[str], values: dict[str, str]) -> list[str]:
    """Şablondaki yer tutucuları doldurur; değeri boşsa parçayı tamamen atar."""
    if not template:
        return []
    for placeholder, value in values.items():
        if f"{{{placeholder}}}" in "".join(template) and not value:
            return []
    return [part.format(**values) for part in template]


def build_command(agent: str, prompt: str, *, task: str, settings: dict) -> tuple[list[str], str | None]:
    """Çalıştırılacak komutu ve (varsa) standart girişten gönderilecek istemi üretir.

    Komut hiçbir zaman kabukla (shell=True) çalıştırılmaz; Windows toplu iş
    dosyaları için ``safe_command`` uygulanır ve taşınamayan istem
    ``CommandTransportError`` ile reddedilir.
    """
    if agent == CUSTOM_AGENT:
        template = custom_command(settings)
        if not template:
            raise ValueError("Özel ajan komutu tanımlı değil.")
        parts = shlex.split(template, posix=False)
        # posix=False tırnakları korur; boşluklu program yolu için yalnız
        # program adındaki tırnaklar atılır.
        parts[0] = resolve_executable(parts[0].strip('"'))
        if any("{prompt}" in part for part in parts):
            return safe_command([part.replace("{prompt}", prompt) for part in parts]), None
        return safe_command(parts), prompt

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
        return safe_command(command), prompt
    command += _expand(profile.get("prompt_args", []), values)
    return safe_command(command), None
