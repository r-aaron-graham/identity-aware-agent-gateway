.PHONY: seed run test

seed:
	python scripts/seed.py

run:
	uvicorn app.main:app --reload

test:
	pytest -q
