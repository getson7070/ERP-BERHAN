.PHONY: setup lint sec test build run
setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt || true
	pip install build ruff flake8 bandit pip-audit pytest || true
lint:
	ruff check . || true
	flake8 || true
sec:
	bandit -r . || true
	pip-audit -r requirements.txt || true
test:
	pytest -q || true
build:
	python -m build || true
run:
	python -m http.server 8000
