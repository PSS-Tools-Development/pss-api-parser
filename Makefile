PSSAPI_DIRECTORY = ../pssapi.py/src/pssapi/
STRUCTURE_FILE = examples/pss_api_complete_structure.json
ENUMS_FILE = examples/pss_enums.json
CACHEABLE_FILE = examples/pss_api_cacheable_endpoints.json
OVERWRITE = 0

# setup
.PHONY: init-dev
init-dev:
	uv self update
	uv python install
	uv sync --no-lock
	uv run pre-commit install
	uv run pre-commit run --all-files

.PHONY: update
update:
	uv sync -U

# formatting and linting
.PHONY: check
check:
	uv run flake8 ./src
	uv run vulture

.PHONY: format
format:
	uv run autoflake .
	uv run isort .
	uv run black .

# testing
.PHONY: test
test:
	uv run pytest ./tests

.PHONY: coverage
coverage:
	uv run pytest --cov=./src/pss_api_parser --cov-report=xml:cov.xml --cov-report=term

# other
.PHONY: requirements
requirements:
	uv sync
	uv pip compile pyproject.toml -o requirements.txt

.PHONY: init
init: ## Install dependencies
	uv sync
