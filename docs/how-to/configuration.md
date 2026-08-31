# Configure models and runtime paths

`Config.from_env()` reads a local `.env` file, then
`SOVEREIGN_AGENT_<FIELD_NAME>` variables. Existing shell variables win over
`.env`.

## Default provider

```bash
export NEBIUS_KEY="..."
sovereign-agent doctor
```

## The `ollama` provider — local Ollama or any OpenAI-compatible endpoint

The `ollama` provider talks to any server that speaks the OpenAI
`/v1/chat/completions` shape: a local Ollama by default, or vLLM, LM Studio, or
OpenAI itself. It reads exactly three variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `SOVEREIGN_AGENT_LLM_BASE_URL` | `http://localhost:11434/v1` | API root; must expose `/chat/completions`. |
| `SOVEREIGN_AGENT_LLM_MODEL` | `qwen3` | Model name (`SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL` is accepted as an alias). |
| `SOVEREIGN_AGENT_LLM_API_KEY` | *(empty)* | Bearer token; blank for local Ollama, set for hosted endpoints. |

Local Ollama (no key needed):

```bash
ollama pull qwen3
export SOVEREIGN_AGENT_LLM_MODEL="qwen3"
sovereign-agent doctor   # lists: ollama  available  qwen3 @ http://localhost:11434/v1
```

A hosted OpenAI-compatible endpoint:

```bash
export SOVEREIGN_AGENT_LLM_BASE_URL="https://api.openai.com/v1"
export SOVEREIGN_AGENT_LLM_MODEL="gpt-4o-mini"
export SOVEREIGN_AGENT_LLM_API_KEY="sk-..."
```

Bind an actor to it by setting that actor's `provider = "ollama"` in
`sovereign.toml`, or at runtime with a ruling actor via
`rebind_actor(actor_id, "ollama", ruler_id)`. The model only *proposes* an
`ActorReport`; the organization re-validates every proposal against the ledger
before anything commits.

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
