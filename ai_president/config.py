import json
import os
from pathlib import Path

from .providers import AI

PATH = Path(os.environ.get("AI_PRESIDENT_CONFIG", Path.home() / ".ai_president" / "config.json"))
FIELDS = ("name", "kind", "base_url", "model", "api_key")


def save(main, assistants, path=PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"main": {k: getattr(main, k) for k in FIELDS},
            "assistants": [{k: getattr(a, k) for k in FIELDS} for a in assistants]}
    path.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(path, 0o600)  # contains API keys
    except OSError:
        pass


def load(path=PATH):
    path = Path(path)
    if not path.exists():
        return None, []
    d = json.loads(path.read_text())
    return AI(**d["main"]), [AI(**a) for a in d["assistants"]]
