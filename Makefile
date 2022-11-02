pssapi:
	python gen.py --structure examples/pss_api_complete_structure.json --enums examples/pss_v0.992_dump_enums.json --out ../pssapi.py/pssapi/ --overwrite
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive ../pssapi.py/pssapi/

check:
	flake8 ../pssapi.py/pssapi/ --count --ignore=E501 --exclude __init__.py --show-source --statistics

.PHONY: pssapi check
