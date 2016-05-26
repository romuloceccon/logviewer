.PHONY: test run

test :
	PYTHONPATH=lib python -m unittest tests

run :
	PYTHONPATH=lib python bin/log-viewer.py
