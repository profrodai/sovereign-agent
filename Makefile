.DEFAULT_GOAL := help

UV ?= uv
PYTHON ?= python3
# Root used only by the explicit run target; verification uses a fresh disposable root.
DEMO_ROOT ?= /tmp/sovereign-agent-first-shift

.PHONY: help help-all setup install test lint format typecheck doctor hooks build run release clean
help: ## Show the first-time guide and five essential commands
	@printf '%s\n' 'Sovereign Agent: learn an always-on Python agent by running a simulated shop.' ''
	@printf '%s\n' 'Start here (Git, make, Python, and uv on PATH):' '  make setup   Install the locked Python 3.12 development environment' '  make doctor  Diagnose prerequisites without installing or changing anything' '  make run     Run a simulated shop; no provider or API key needed' '  make verify  Run the full gate on your build host' '  make hooks   Install the lightweight guard against direct pushes to main' ''
	@printf '%s\n' 'make help-all lists every target. Set DEMO_ROOT to choose your demo data directory.' 'Setup/build can download dependencies. Doctor is offline; run writes demo receipts.'

help-all: ## List every supported target and its description
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z][a-zA-Z0-9_-]*:.*## / {printf "  %-13s %s\n", $$1, $$2}' Makefile

setup: ## Sync locked dependencies and Python 3.12 with uv (network may be needed)
	$(UV) sync --locked --python 3.12 --group dev

install: setup ## Compatibility alias for setup

test: ## Run deterministic tests; live provider tests remain deselected
	$(UV) run --python 3.12 python -m pytest -q

format: ## Check Python formatting without rewriting files
	$(UV) run --python 3.12 ruff format --check src tests scripts

typecheck: ## Check the public runtime with strict mypy
	$(UV) run --python 3.12 mypy src/sovereign_agent

lint: format typecheck ## Check formatting, Ruff rules, and runtime types
	$(UV) run --python 3.12 ruff check src tests scripts

doctor: ## Read-only tool, pinned Python/dependency, and installed-hook diagnosis
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { printf '%s\n' 'FIX install Python 3.12+ or set PYTHON to an existing interpreter'; exit 1; }
	@$(PYTHON) -B scripts/development.py doctor

hooks: ## Install the main-push guard; refuse to overwrite existing hook policy
	$(PYTHON) -B scripts/development.py hooks

build: ## Build wheel and source distribution in dist (network may be needed)
	$(UV) build --python 3.12

run: ## Run the offline simulated store demo, writing receipts under DEMO_ROOT
	$(UV) run --python 3.12 sovereign-agent demo store --mode simulated --root "$(DEMO_ROOT)"

release: verify build ## Prepare verified release artifacts; publishing stays in the tag workflow
	@printf '%s\n' 'Release artifacts are in dist/.' 'Authorized version tags use the existing publish workflow and protected PyPI environments.' 'This target does not push a tag, create a release, or publish packages.'

clean: ## Remove ignored build/tool outputs only; keep virtual environment and learner data
	$(PYTHON) -B scripts/development.py clean

.PHONY: verify
verify: lint test ## Run the full offline gate and fresh README onboarding
	$(UV) run --python 3.12 python scripts/verify_runtime_dependencies.py
	$(UV) run --python 3.12 python scripts/verify_source_budget_v2.py
	$(UV) run --python 3.12 sovereign-agent --help >/dev/null
	$(UV) run --python 3.12 sovereign-agent doctor
	@set -eu; demo_parent=$${TMPDIR:-/tmp}; demo_parent=$${demo_parent%/}; \
	demo_root=$$(mktemp -d "$$demo_parent/sovereign-agent-demo.XXXXXXXX") || exit $$?; \
	test -n "$$demo_root" && test -d "$$demo_root" || exit 1; \
	case "$$demo_root" in "$$demo_parent"/sovereign-agent-demo.*) ;; *) exit 1;; esac; \
	trap 'result=$$?; trap - EXIT; rm -rf -- "$$demo_root"; exit "$$result"' EXIT; \
	trap 'exit 130' INT; trap 'exit 143' TERM; \
	$(UV) run --python 3.12 sovereign-agent demo store --mode simulated --root "$$demo_root"
	$(UV) run --python 3.12 python scripts/verify_readme_onboarding_v3.py
