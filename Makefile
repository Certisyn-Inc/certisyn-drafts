DRAFT   := draft-hillier-scitt-arp
MD      := $(DRAFT).md
XML     := $(DRAFT).xml
TXT     := $(DRAFT).txt
HTML    := $(DRAFT).html

KRAMDOWN := $(shell command -v kramdown-rfc2629 2>/dev/null || command -v kramdown-rfc 2>/dev/null)
XML2RFC  := $(shell command -v xml2rfc 2>/dev/null)

.PHONY: all html lint clean check-tools check-docname

all: $(TXT)

$(XML): $(MD) check-tools
	$(KRAMDOWN) $(MD) > $(XML)

$(TXT): $(XML)
	$(XML2RFC) --text $(XML)

html: $(XML)
	$(XML2RFC) --html $(XML)

# DEFECT FIX (Songbo, 2026-07-29). This passed --verbose, which current idnits
# does not accept, so the documented lint command exited on an option error and
# ran no validation at all. A lint target that cannot fail is not a lint target.
# --nitcount reports the counts; a missing idnits is still tolerated, but an
# idnits that RUNS and reports errors now fails the target.
lint: $(TXT)
	@if command -v idnits >/dev/null 2>&1; then \
	  idnits --nitcount $(TXT); \
	else \
	  echo "idnits not installed - use https://author-tools.ietf.org/idnits"; \
	fi

# The failure that lost -01: the source said -00 while the datatracker said -01.
check-docname:
	@grep -E '^docname:' $(MD) || (echo "no docname in $(MD)"; exit 1)
	@echo "Confirm the revision above is the one you intend to file."

check-tools:
	@test -n "$(KRAMDOWN)" || (echo "ERROR: kramdown-rfc2629 not found."; \
	  echo "  gem install kramdown-rfc2629"; \
	  echo "  or build via https://author-tools.ietf.org/ (see BUILD-AND-SUBMIT.md)"; \
	  exit 1)
	@test -n "$(XML2RFC)" || (echo "ERROR: xml2rfc not found. pip install xml2rfc"; exit 1)

clean:
	rm -f $(XML) $(TXT) $(HTML)
