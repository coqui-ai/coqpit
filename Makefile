.DEFAULT_GOAL := help
.PHONY: style lint install help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

target_dirs := tests coqpit


test:	## run tests.
	nosetests -x --with-cov -cov  --cover-erase --cover-package coqpit tests --nologcapture --nocapture

style:	## update code style.
	black ${target_dirs}
	isort ${target_dirs}

lint:	## run pylint linter.
	pylint ${target_dirs}

install:	## install 👩‍✈️ Coqpit for development.
	pip install -e .
