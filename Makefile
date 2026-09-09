.DEFAULT_GOAL := help

UV ?= uv

.PHONY: help
help:
	@printf "Sovereign Agent educational development\n\n"
	@printf "  make install   Sync Python 3.14 and development tools\n"
	@printf "  make verify    Check runtime, active book and historical compatibility\n"
	@printf "  make test      Run tests\n"
	@printf "  make lint      Run Ruff and mypy\n"
	@printf "  make doctor    Check the offline learner environment\n"
	@printf "  make labs      Execute archived companion labs from fresh roots\n"
	@printf "  make exercises Execute active exercise and solution notebooks\n"

.PHONY: install
install:
	$(UV) sync --python 3.14 --group dev

.PHONY: test
test:
	$(UV) run --python 3.14 python -m pytest -q

.PHONY: lint
lint:
	$(UV) run --python 3.14 ruff format --check src tests scripts book
	$(UV) run --python 3.14 ruff check src tests scripts book
	$(UV) run --python 3.14 mypy src/sovereign_agent

.PHONY: doctor
doctor:
	$(UV) run --python 3.14 sovereign-agent doctor

.PHONY: labs
labs:
	$(UV) run --python 3.14 python scripts/book_archive_support_v1.py labs

.PHONY: exercises
exercises:
	$(UV) run --python 3.14 --group authoring python scripts/verify_book_assets_v1.py --check-execution
	$(UV) run --python 3.14 python scripts/package_book_assets_v1.py --verify

.PHONY: verify
verify: lint test
	$(UV) run --python 3.14 python scripts/verify_runtime_dependencies.py
	$(UV) run --python 3.14 python scripts/verify_source_budget_v2.py
	$(UV) run --python 3.14 python scripts/book_archive_support_v1.py gates
	$(UV) run --python 3.14 python scripts/verify_book_assets_v1.py --textbook
	$(UV) run --python 3.14 python scripts/verify_book_assets_v1.py
	$(UV) run --python 3.14 python scripts/package_book_assets_v1.py --verify
	$(UV) run --python 3.14 sovereign-agent --help >/dev/null
	$(UV) run --python 3.14 sovereign-agent doctor
	$(UV) run --python 3.14 sovereign-agent demo store --mode simulated --root /tmp/sovereign-agent-demo
	$(UV) run --python 3.14 python scripts/verify_readme_onboarding_v3.py
