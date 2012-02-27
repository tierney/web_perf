all:
	@echo
	@echo See README.

setup:
	./virtualenv.py --distribute --no-site-packages -v .

clean:
	rm -f *.pyc

deepclean: clean
	rm -rf bin lib share local
