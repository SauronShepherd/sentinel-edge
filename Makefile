.PHONY: setup format-check lint type architecture governance gates test-all-modules contracts plugins
setup:
	python -m pip install --no-build-isolation -e contracts/sentinel-contracts -e sdk/sentinel-plugin-sdk -e sdk/sentinel-testkit
format-check:
	python -m compileall -q scripts contracts sdk
lint:
	python -m pytest -q contracts/sentinel-contracts/tests sdk/sentinel-plugin-sdk/tests sdk/sentinel-testkit/tests tests --junitxml=build/test-results/all.xml
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
	pytest -q contracts/sentinel-contracts/tests tests sdk/sentinel-plugin-sdk/tests sdk/sentinel-testkit/tests
generate-contracts:
	python scripts/generate_contracts.py
gates: generate-contracts format-check lint type architecture governance contracts plugins test-all-modules
inject-failure-proof:
	python scripts/prove_gate_failures.py failure
inject-skip-proof:
	python scripts/prove_gate_failures.py skip
test-arm:
	@echo "Arm gate planned: no hardware claim made"
