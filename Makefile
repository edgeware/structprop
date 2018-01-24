all:

test:
	tox

clean:
	$(RM) -r *.egg-info build
