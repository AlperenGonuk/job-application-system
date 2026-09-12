"""Alt süreçleri kullanıcıya konsol penceresi göstermeden çalıştırmak için yardımcılar.

Uygulama ilan toplama ve yapay zeka işlerini ayrı süreçte çalıştırır. Windows'ta
bu süreçler varsayılan olarak kısa süreliğine siyah bir konsol penceresi açar;
kullanıcılar bunu zararlı yazılım davranışı sanabilir. Buradaki seçenekler
pencereyi hiç açtırmaz. Diğer işletim sistemlerinde ek bir şey gerekmez.
"""
from __future__ import annotations

import subprocess
import sys


def hidden_process_options() -> dict:
    """subprocess çağrılarına eklenecek, pencere açmayan seçenekler."""
    if not sys.platform.startswith("win"):
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {"creationflags": subprocess.CREATE_NO_WINDOW, "startupinfo": startup}
