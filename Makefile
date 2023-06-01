PSSAPI_DIRECTORY = ../pssapi.py/src/pssapi/
STRUCTURE_FILE = examples/pss_api_complete_structure.json
ENUMS_FILE = examples/pss_enums.json
CACHEABLE_FILE = examples/pss_api_cacheable_endpoints.json
OVERWRITE = 0

.PHONY: help
help: ## Display this help screen
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## Install dependencies
	poetry install

.PHONY: pssapi
pssapi: gen ## Generate, auto-lint pssapi.py and check errors

.PHONY: gen
gen: ## Generate the code
ifeq ($(OVERWRITE), 1)
	poetry run python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --cacheable ${CACHEABLE_FILE} --out $(PSSAPI_DIRECTORY) --overwrite
else
	poetry run python gen.py --structure $(STRUCTURE_FILE) --enums $(ENUMS_FILE) --cacheable ${CACHEABLE_FILE} --out $(PSSAPI_DIRECTORY)
endif
