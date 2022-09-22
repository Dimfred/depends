.PHONY: env
env: ##      enable venv
	@python3.9 -m poetry shell

.PHONY: test
test: ##     run the tests
	@python3 -m pytest -s

.PHONY: cov
cov: ##      run coverage
	@python3 -m pytest -s \
		-p no:pytest-brownie \
		--cov-report term-missing \
		--cov-config pytest.ini \
		--cov=. tests/

.PHONY: help
help: ##     show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
