"""Interactive setup wizard: choose main AI and any number of assistant AIs."""
import webbrowser

from . import config
from .providers import CATALOG, AI, from_catalog


def _ask(msg, default=""):
    v = input(f"{msg}{' [' + default + ']' if default else ''}: ").strip()
    return v or default


def _pick(msg):
    names = list(CATALOG)
    for i, n in enumerate(names, 1):
        print(f"  {i:2}. {n:11} model={CATALOG[n]['model']:36} get a key: {CATALOG[n]['url']}")
    print(f"  {len(names) + 1:2}. custom (any OpenAI-compatible API)")
    while True:
        c = _ask(msg)
        if c.isdigit() and 1 <= int(c) <= len(names) + 1:
            return int(c) - 1 if int(c) <= len(names) else None
        print("Please enter a number from the list.")


def _build(idx):
    if idx is None:
        name = _ask("Name for this AI")
        return AI(name=name, kind="openai", base_url=_ask("Base URL (e.g. https://host/v1)"),
                  model=_ask("Model"), api_key=_ask("API key (blank if none)"))
    preset = list(CATALOG)[idx]
    url = CATALOG[preset]["url"]
    print(f"\nYou can get an API key for {preset} at: {url}")
    if _ask("Open this page in a browser? (y/n)", "n").lower().startswith("y"):
        try:
            webbrowser.open(url)
        except Exception:
            pass
    key = "" if preset == "ollama" else _ask(f"Paste your {preset} API key")
    return from_catalog(preset, key, model=_ask("Model", CATALOG[preset]["model"]))


def run():
    print("=== AI-President setup wizard ===\n\nStep 1: choose the MAIN AI (synthesizes options, clerks consensus).")
    main = _build(_pick("Main AI number"))
    print("\nStep 2: add assistant AIs (as many as you like) that process the problem via API.")
    assistants = []
    while True:
        assistants.append(_build(_pick(f"Assistant #{len(assistants) + 1} number")))
        if not _ask("Add another assistant? (y/n)", "y").lower().startswith("y"):
            break
    config.save(main, assistants)
    print(f"\nSaved to {config.PATH}")
    return main, assistants
