.PHONY: test

test :
	PYTHONPATH=lib python -m unittest tests
