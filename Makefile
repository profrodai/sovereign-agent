.DEFAULT_GOAL := help

UV ?= uv

.PHONY: help
help:
	@printf "Sovereign Agent educational development\n\n"
	@printf "  make install   Sync Python 3.12 (Colab's) and development tools\n"
	@printf "  make verify    Check the runtime, tests, lint and README onboarding\n"
	@printf "  make test      Run tests\n"
	@printf "  make lint      Run Ruff and mypy\n"
	@printf "  make doctor    Check the offline learner environment\n"

.PHONY: install
install:
	$(UV) sync --python 3.12 --group dev

.PHONY: test
test:
	$(UV) run --python 3.12 python -m pytest -q

.PHONY: lint
lint:
	$(UV) run --python 3.12 ruff format --check src tests scripts
	$(UV) run --python 3.12 ruff check src tests scripts
	$(UV) run --python 3.12 mypy src/sovereign_agent

.PHONY: doctor
doctor:
	$(UV) run --python 3.12 sovereign-agent doctor

.PHONY: verify
verify: lint test
	$(UV) run --python 3.12 python scripts/verify_runtime_dependencies.py
	$(UV) run --python 3.12 python scripts/verify_source_budget_v2.py
	$(UV) run --python 3.12 sovereign-agent --help >/dev/null
	$(UV) run --python 3.12 sovereign-agent doctor
	$(UV) run --python 3.12 sovereign-agent demo store --mode simulated --root /tmp/sovereign-agent-demo
	$(UV) run --python 3.12 python scripts/verify_readme_onboarding_v3.py
