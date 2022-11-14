PSSAPI_DIRECTORY = ../pssapi.py/pssapi/
STRUCTURE_FILE = examples/pss_api_complete_structure.json
ENUMS_FILE = examples/pss_v0.992_dump_enums.json
OVERWRITE = 1

.PHONY: help
help: ## Display this help screen
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: env
env: ## Create virtualenv and install dependencies
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

.PHONY: pssapi
pssapi: gen lint check ## Generate, auto-lint pssapi.py and check errors

.PHONY: gen
gen: ## Generate the code
ifeq ($(OVERWRITE), 1)
	python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --out $(PSSAPI_DIRECTORY) --overwrite
else
	python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --out $(PSSAPI_DIRECTORY)
endif

.PHONY: lint
lint: ## Auto-lint the generated code
	autopep8 --in-place --max-line-length 200 --recursive $(PSSAPI_DIRECTORY)
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive $(PSSAPI_DIRECTORY)

.PHONY: check
check: ## Check Python syntax commons errors of the generated code
	flake8 $(PSSAPI_DIRECTORY) --count --ignore=E501 --exclude __init__.py --show-source --statistics
