.DEFAULT_GOAL := help
.PHONY: clean build help

VENV_NAME=venv_cryptowatson-indicators

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d ${VENV_NAME} || python3 -m venv ${VENV_NAME}
	. ${VENV_NAME}/bin/activate; pip3 install -Ur requirements.txt
	touch ${VENV_NAME}/touchfile

### activate environment, install requirements and local package (.)
install: venv
	. ${VENV_NAME}/bin/activate; pip3 install -e .

### activate environment, install requirements an install ipython kernel in venv
install-ipython-kernel: venv
#	. ${VENV_NAME}/bin/activate; ipython kernel install --user --name=venv
	. ${VENV_NAME}/bin/activate; python3 -m ipykernel install --user --name=venv

### activate environment, install requirements and run tests
test: venv
	. ${VENV_NAME}/bin/activate; python3 setup.py pytest

### autogenerate imports in __init__.py files. --noattrs --nomods --relative --recursive
mkinit: venv
	. ${VENV_NAME}/bin/activate; mkinit cryptowatson_indicators --nomods --relative --recursive  -w
	. ${VENV_NAME}/bin/activate; mkinit cryptowatson_indicators -w

### activate environment, install requirements and build package
build: mkinit
	. ${VENV_NAME}/bin/activate; python3 setup.py bdist_wheel

### Clean logs and resources
clean:
	rm -r ./logs/*
	rm -rf ${VENV_NAME}

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
