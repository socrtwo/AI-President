"""Provider catalog and minimal HTTP clients (stdlib only, so it runs on Android/Termux)."""
import json
import urllib.request
from dataclasses import dataclass, field

# kind: "openai" (OpenAI-compatible chat API), "anthropic", "gemini", "mock"
CATALOG = {
    "openai": dict(kind="openai", base_url="https://api.openai.com/v1", model="gpt-4o-mini",
                   url="https://platform.openai.com/api-keys"),
    "anthropic": dict(kind="anthropic", base_url="https://api.anthropic.com/v1", model="claude-3-5-haiku-latest",
                      url="https://console.anthropic.com/settings/keys"),
    "gemini": dict(kind="gemini", base_url="https://generativelanguage.googleapis.com/v1beta",
                   model="gemini-1.5-flash", url="https://aistudio.google.com/app/apikey"),
    "mistral": dict(kind="openai", base_url="https://api.mistral.ai/v1", model="mistral-small-latest",
                    url="https://console.mistral.ai/api-keys"),
    "groq": dict(kind="openai", base_url="https://api.groq.com/openai/v1", model="llama-3.1-8b-instant",
                 url="https://console.groq.com/keys"),
    "deepseek": dict(kind="openai", base_url="https://api.deepseek.com/v1", model="deepseek-chat",
                     url="https://platform.deepseek.com/api_keys"),
    "xai": dict(kind="openai", base_url="https://api.x.ai/v1", model="grok-2-latest",
                url="https://console.x.ai"),
    "openrouter": dict(kind="openai", base_url="https://openrouter.ai/api/v1", model="meta-llama/llama-3.1-8b-instruct",
                       url="https://openrouter.ai/keys"),
    "together": dict(kind="openai", base_url="https://api.together.xyz/v1",
                     model="meta-llama/Llama-3.1-8B-Instruct-Turbo", url="https://api.together.ai/settings/api-keys"),
    "perplexity": dict(kind="openai", base_url="https://api.perplexity.ai", model="sonar",
                       url="https://www.perplexity.ai/settings/api"),
    "ollama": dict(kind="openai", base_url="http://localhost:11434/v1", model="llama3.1",
                   url="https://ollama.com/download"),
}


@dataclass
class AI:
    """One configured AI. Any number may be configured; any may be the main one."""
    name: str
    kind: str = "openai"
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    responses: list = field(default_factory=list)  # only used by kind="mock"

    def ask(self, prompt, system="You are a careful, honest advisor.", timeout=120):
        if self.kind == "mock":
            return self.responses.pop(0) if self.responses else ""
        if self.kind == "openai":
            url = self.base_url.rstrip("/") + "/chat/completions"
            body = {"model": self.model, "messages": [{"role": "system", "content": system},
                                                      {"role": "user", "content": prompt}]}
            headers = {"Authorization": "Bearer " + self.api_key}
            return _post(url, body, headers, timeout)["choices"][0]["message"]["content"]
        if self.kind == "anthropic":
            url = self.base_url.rstrip("/") + "/messages"
            body = {"model": self.model, "max_tokens": 2048, "system": system,
                    "messages": [{"role": "user", "content": prompt}]}
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            return "".join(b.get("text", "") for b in _post(url, body, headers, timeout)["content"])
        if self.kind == "gemini":
            url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent"
            body = {"system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            headers = {"x-goog-api-key": self.api_key}
            r = _post(url, body, headers, timeout)
            return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
        raise ValueError(f"Unknown provider kind: {self.kind}")


def _post(url, body, headers, timeout):
    h = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, json.dumps(body).encode(), h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def from_catalog(preset, api_key="", name=None, model=None):
    c = CATALOG[preset]
    return AI(name=name or preset, kind=c["kind"], base_url=c["base_url"],
              model=model or c["model"], api_key=api_key)
