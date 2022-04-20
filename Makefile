reformat:
	@black .
	@isort .

lint:
	@flakehell lint . --count
	@mypy .

clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

wheel:
	@pip wheel . -w dist --no-deps

build:
	@pip wheel . -w dist --no-deps
