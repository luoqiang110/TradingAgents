.DEFAULT_GOAL := help

ifeq ($(OS),Windows_NT)
PYTHON_BOOT ?= python
else
PYTHON_BOOT ?= python3
endif

.PHONY: help setup doctor config config-upgrade check install setup-sandbox ubuntu-bootstrap dev dev-daemon start start-daemon stop clean

help setup doctor config config-upgrade check install setup-sandbox ubuntu-bootstrap dev dev-daemon start start-daemon stop clean:
	@$(PYTHON_BOOT) scripts/make_tasks.py $@
