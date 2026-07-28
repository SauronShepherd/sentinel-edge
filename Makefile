.PHONY: setup format-check lint type architecture governance gates test-all-modules contracts plugins
setup:
	python -m pip install -e contracts/sentinel-contracts -e sdk/sentinel-plugin-sdk -e sdk/sentinel-testkit
format-check:
	python -m compileall -q scripts contracts sdk
lint:
	python -m pytest -q --junitxml=build/test-results/all.xml
	python scripts/check_no_silent_skips.py build/test-results/all.xml
type:
	python scripts/check_python_types.py
architecture:
	python scripts/check_architecture_boundaries.py
governance:
	pytest -q tests/governance
contracts:
	python scripts/generate_contracts.py
	pytest -q tests/contracts
plugins:
	pytest -q sdk/sentinel-plugin-sdk/tests
test-all-modules:
	pytest -q tests sdk/sentinel-plugin-sdk/tests sdk/sentinel-testkit/tests
gates: format-check lint type architecture governance contracts plugins test-all-modules
