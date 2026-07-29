# Don't Leave the Sky Guessing — Build Tooling
#
# Targets:
#   pdf          Build the PDF (version from VERSION file or "draft")
#   pdf-version  Build PDF with a specific version: make pdf-version V=1.0.0
#   clean        Remove build artifacts
#   view         Open the PDF with system viewer (Linux only)

BUILD_DIR = .
VENV_DIR ?= /tmp/pdf-venv
VERSION_FILE = VERSION

# Determine version
ifdef V
    VERSION := $(V)
else ifneq (,$(wildcard $(VERSION_FILE)))
    VERSION := $(shell cat $(VERSION_FILE))
else
    VERSION := draft
endif

PDF_OUTPUT = $(BUILD_DIR)/dont-leave-the-sky-guessing-$(VERSION).pdf
HTML_OUTPUT = $(BUILD_DIR)/dont-leave-the-sky-guessing-$(VERSION).html

.PHONY: pdf pdf-setup pdf-version clean view

pdf: $(PDF_OUTPUT)

pdf-setup:
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install -r requirements-pdf.txt

$(PDF_OUTPUT): $(wildcard *.md) build-pdf.py
	@echo "Building PDF version $(VERSION)..."
	. $(VENV_DIR)/bin/activate && python3 build-pdf.py --version $(VERSION)
	@echo "Done: $(PDF_OUTPUT)"

pdf-version:
	$(MAKE) pdf V=$(V)

clean:
	rm -f $(BUILD_DIR)/dont-leave-the-sky-guessing-*.pdf
	rm -f $(BUILD_DIR)/dont-leave-the-sky-guessing-*.html
	@echo "Cleaned build artifacts"

view: $(PDF_OUTPUT)
	xdg-open $(PDF_OUTPUT) 2>/dev/null || \
		open $(PDF_OUTPUT) 2>/dev/null || \
		echo "Open $(PDF_OUTPUT) manually"
