all:

test:
	python setup.py test

check:
	pep8 structprop

clean:
	rm -rf *.egg-info
