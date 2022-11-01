pssapi:
	python gen.py --flows examples/pss_api_steam_v0.991.4_anonymized.json --enums examples/pss_v0.992_dump_enums.json --out ../pssapi.py/pssapi/ --overwrite
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive ../pssapi.py/pssapi/
	flake8 ../pssapi.py/pssapi/ --count --ignore=E501 --exclude __init__.py --show-source --statistics

.PHONY: pssapi