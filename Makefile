.PHONY: test install run

test :
	python -m unittest discover -s tests -p '*_test.py'

install :
	pip install -e .

run :
	logviewer conf.conf
