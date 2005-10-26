#
# Makefile for documentation.
#

PYTHON = python

# This specifies the executables for my system.
# setenv RST2HTML to rst2html.py to test the documentation conversion.
RST2HTML ?= projects-rst2html --project-header 
RST2HTML_PROJHOME = --project-home

SIMPLE_REST_SOURCES =				\
	handpath.txt				\
	tutorial.txt				\
	design.txt				\
	develop.txt				\
	faq.txt 

OUTPUTS = ../index.html $(SIMPLE_REST_SOURCES:.txt=.html) fields.html

.SUFFIXES: .txt .html

all : $(OUTPUTS)

# Auto-generated fields.
fields.html: $(wildcard ../lib/python/atocha/fields/*.py) \
		../lib/python/atocha/field.py \
		atocha-gen-fields-doc.py
	$(PYTHON) atocha-gen-fields-doc.py

# Home page.
../index.html : ../README
	$(RST2HTML) $< $@

# Other documentation pages.
$(SIMPLE_REST_SOURCES:.txt=.html) : %.html : %.txt
	$(RST2HTML) $(RST2HTML_PROJHOME)=.. $< $@

clean:
	rm -f $(OUTPUTS)
