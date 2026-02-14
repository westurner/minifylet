.PHONY: all test clean

PYTHON ?= python3
MINIFYLET = $(PYTHON) -m minifylet.cli
MINIFY_CLIPBOARD_ARGS = -C

DATA_DIR = tests/data

# Find all .js files that are not .min.js
SOURCES := $(filter-out %.min.js, $(wildcard $(DATA_DIR)/*.js))
# Define targets by replacing .js with .min.js
TARGETS := $(SOURCES:.js=.min.js)

default: all

all: $(TARGETS)

install:
	python3 -m pip install -e .[dev]

test:
	pytest

# Parametrized rule to generate any .min.js from .js
%.min.js: %.js
	$(MINIFYLET) $(MINIFY_CLIPBOARD_ARGS) --check-js $< $@

# Explicit targets for convenience (pointing to the generated files)
searchforthis_google: $(DATA_DIR)/searchforthis_google-bookmarklet.min.js
searchforthis_google_scholar: $(DATA_DIR)/searchforthis_google_scholar-bookmarklet.min.js
toggleshowvisited: $(DATA_DIR)/toggleshowvisited-bookmarklet.min.js

clean:
	rm -f $(TARGETS)
