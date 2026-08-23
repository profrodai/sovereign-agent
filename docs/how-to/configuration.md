# Configure models and runtime paths

`Config.from_env()` reads a local `.env` file, then
`SOVEREIGN_AGENT_<FIELD_NAME>` variables. Existing shell variables win over
`.env`.

## Default provider

```bash
export NEBIUS_KEY="..."
sovereign-agent doctor
```

## Another OpenAI-compatible provider

```bash
export OPENAI_API_KEY="..."
export SOVEREIGN_AGENT_LLM_BASE_URL="https://api.openai.com/v1/"
export SOVEREIGN_AGENT_LLM_API_KEY_ENV="OPENAI_API_KEY"
export SOVEREIGN_AGENT_LLM_PLANNER_MODEL="gpt-4o"
export SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL="gpt-4o-mini"
```

## Local Ollama

Pull the configured models first, then:

```bash
export OLLAMA_API_KEY="ollama"
export SOVEREIGN_AGENT_LLM_BASE_URL="http://localhost:11434/v1/"
export SOVEREIGN_AGENT_LLM_API_KEY_ENV="OLLAMA_API_KEY"
export SOVEREIGN_AGENT_LLM_PLANNER_MODEL="qwen2.5:32b"
export SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL="qwen2.5:14b"
```

## Store sessions elsewhere

```bash
export SOVEREIGN_AGENT_SESSIONS_DIR="/srv/sovereign-agent/sessions"
export SOVEREIGN_AGENT_RUNTIME_DIR="/srv/sovereign-agent/runtime"
```

Paths must have writable parents. Run `sovereign-agent doctor --skip-llm` to
validate local setup without calling a provider.

## TOML

```toml
[sovereign_agent]
sessions_dir = "sessions"
max_concurrent = 3
engage_mode = "interactive"
worker_backend = "bare"
```

Load it with `Config.from_toml(Path("agent.toml"))`. Do not commit credentials
to TOML or `.env`; configuration stores the *name* of the key variable.
