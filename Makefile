.PHONY: help mypy


help:
	@echo "mypy - Run static type checking"
#	@echo "pytype - Run static type checking"
#	@echo "pyright - Run static type checking"
#	@echo "pyre - Run static type checking"

mypy:
	mypy oneaway.py
