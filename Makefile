PSSAPI_DIRECTORY = ../pssapi.py/src/pssapi/
STRUCTURE_FILE = examples/pss_api_complete_structure.json
ENUMS_FILE = examples/pss_steam_v0.994.1.8792_dump_enums.json
CACHEABLE_FILE = examples/pss_api_cacheable_endpoints.json
OVERWRITE = 1

.PHONY: help
help: ## Display this help screen
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## Install dependencies
	pip install --upgrade pip
	pip install pip-tools
	pip-sync requirements.txt

.PHONY: pssapi
pssapi: gen ## Generate, auto-lint pssapi.py and check errors

.PHONY: gen
gen: ## Generate the code
ifeq ($(OVERWRITE), 1)
	python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --cacheable ${CACHEABLE_FILE} --out $(PSSAPI_DIRECTORY) --overwrite
else
	python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --cacheable ${CACHEABLE_FILE} --out $(PSSAPI_DIRECTORY)
endif

.PHONY: requirements
requirements: ## Compile requirements.txt with pip-tools
	CUSTOM_COMPILE_COMMAND="make requirements" pip-compile --resolver=backtracking requirements.in
