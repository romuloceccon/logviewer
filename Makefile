.PHONY: test run

test :
	python -m unittest discover -s tests -p '*_test.py'

run :
	PYTHONPATH=. python bin/log-viewer.py conf.conf
