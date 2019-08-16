tests=$(shell find test -name test*.py)
targets=$(tests:%.py=%.done)

.PHONY: all clean

all: cov.xml

cov.xml: $(targets)
	coverage xml -o cov.xml

test/%.done: test/%.py
	coverage run -a -m pytest $<
	touch $@

clean:
	rm -f $(targets)
