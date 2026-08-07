# Don't Leave the Sky Guessing — Build Tooling
#
# Targets:
#   book         Build the PDF and EPUB publication edition
#   pdf          Build the PDF
#   epub         Build the EPUB
#   clean        Remove build artifacts

BUILD_DIR = .
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
EPUB_OUTPUT = $(BUILD_DIR)/dont-leave-the-sky-guessing-$(VERSION).epub

.PHONY: book pdf epub pdf-version clean view

book:
	python3 build-pdf.py --version $(VERSION)

pdf: book

epub: book

pdf-version:
	$(MAKE) pdf V=$(V)

clean:
	rm -f $(BUILD_DIR)/dont-leave-the-sky-guessing-*.pdf
	rm -f $(BUILD_DIR)/dont-leave-the-sky-guessing-*.epub
	rm -f $(BUILD_DIR)/dont-leave-the-sky-guessing-*.html
	rm -rf .build
	@echo "Cleaned publication artifacts"

view: book
	xdg-open $(PDF_OUTPUT) 2>/dev/null || \
		open $(PDF_OUTPUT) 2>/dev/null || \
		echo "Open $(PDF_OUTPUT) manually"
