.PHONY: setup seed run test lint docker docker-run

setup:
	python -m pip install -r requirements-dev.txt

seed:
	python scripts/seed.py

run:
	uvicorn app.main:app --reload

test:
	pytest -q --cov=app --cov-report=term-missing

lint:
	ruff check .

docker:
	docker build -t identity-aware-agent-gateway:local .

docker-run: docker
	docker run --rm -p 8000:8000 identity-aware-agent-gateway:local
