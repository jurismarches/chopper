tests:
	pytest -s .

styles:
	isort chopper
	black .
	flake8 --config setup.cfg

styles.check:
	black . --check
	isort chopper --check-only
	flake8 --config setup.cfg

doc:
	(cd docs; make html)
