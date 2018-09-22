PYTHON := python3.6
NAME := $(shell $(PYTHON) setup.py --name)
VERSION = $(shell $(PYTHON) setup.py --version)

SDIST = dist/$(NAME)-$(VERSION).tar.gz
WHEEL = dist/$(NAME)-$(VERSION)-py3-none-any.whl
SOURCE = setup.py MANIFEST.in $(shell find queues -type f -print)

export DJANGO_DEBUG

all: $(SDIST) $(WHEEL)

$(SDIST): $(SOURCE)
	$(PYTHON) setup.py sdist

sdist: $(SDIST)

$(WHEEL): $(SOURCE)
	$(PYTHON) setup.py bdist_wheel

wheel: $(WHEEL)

test:
	tox -e py36-django21

clean:
	rm -rf .tox build dist
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -delete


.PHONY: all clean sdist test wheel
