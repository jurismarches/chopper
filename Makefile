tests:
	nosetests --with-coverage --cover-package=chopper

styles:
	isort chopper
	black .
	flake8 --config setup.cfg

styles.check:
	black . --check
	isort --ws jurismarches --check-only
	flake8 --config setup.cfg
