# AI-President
Android-only AI decision maker that weighs presidential precedent, philosophy, political science, religion (mainly Christianity), science, public intelligence, AI, social media and odds markets to suggest options with cost and timeline estimates. Horoscopes used only for jokes.

## Usage (Python 3.8+, no dependencies; works on Android via Termux)
    python -m ai_president --setup          # wizard: pick the main AI (with links to get API keys) + any number of assistant AIs
    python -m ai_president "Your decision"  # --mode suggest|vote|quaker|all (default all)

1. Assistant AIs each analyze the problem via their APIs.
2. The main AI synthesizes all answers into a list of options and suggests its best choice.
3. **Vote**: every AI (main included) votes on all options; the most votes wins (ties are reported).
4. **Quaker consensus**: all AIs speak, the main AI clerks a minute, and each approves, stands aside, or blocks; concerns carry into further rounds until there is unity.

Supported presets: OpenAI, Anthropic, Gemini, Mistral, Groq, DeepSeek, xAI, OpenRouter, Together, Perplexity, Ollama, plus any custom OpenAI-compatible endpoint. Config (with API keys) is stored at `~/.ai_president/config.json` (mode 600). Run tests: `python -m unittest discover -s tests`.
