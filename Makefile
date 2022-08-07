.DEFAULT_GOAL := help
.PHONY: clean build help

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip3 install -Ur requirements.txt
	touch venv/touchfile

### activate environment, install requirements and local package (.)
install: venv
	. venv/bin/activate; pip3 install -e .

### activate environment, install requirements an install ipython kernel in venv
install-ipython-kernel: venv
	ipython kernel install --user --name=venv

### activate environment, install requirements and run tests
test: venv
	. venv/bin/activate; python3 setup.py pytest

### activate environment, install requirements and build package
build: venv
	. venv/bin/activate; python3 setup.py bdist_wheel

### Clean logs and resources
clean:
	rm -r ./logs/*
	rm -rf venv

# show help: Renders automatically categories (##) and targets (###). Regular comments (#) ignored
# Based on: https://gist.github.com/prwhite/8168133?permalink_comment_id=2278355#gistcomment-2278355
TARGET_COLOR := $(shell tput -Txterm setaf 6)
BOLD := $(shell tput -Txterm bold)
RESET := $(shell tput -Txterm sgr0)
help:
	@echo ''
	@echo 'Usage:'
	@echo '  make ${TARGET_COLOR}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^### (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 4, RLENGTH); \
      printf "  ${TARGET_COLOR}%-20s${RESET} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)
