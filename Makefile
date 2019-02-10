#
# Project:   weechat-notify-send
# Copyright: (c) 2015 by Petr Zemek <s3rvac@gmail.com> and contributors
# License:   MIT, see the LICENSE file for more details
#
# A GNU Makefile for the project.
#

.PHONY: help clean lint tests tests-coverage

help:
	@echo "Use \`make <target>', where <target> is one of the following:"
	@echo "  clean          - remove all generated files"
	@echo "  lint           - check code style with flake8"
	@echo "  tests          - run tests"
	@echo "  tests-coverage - obtain test coverage"

clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.py[co]' -exec rm -f {} +
	@rm -rf .coverage coverage

lint:
	@flake8 --ignore=E402,W504 --max-line-length=100 notify_send.py notify_send_tests.py

tests:
	@nosetests notify_send_tests.py

tests-coverage:
	@nosetests notify_send_tests.py \
		--with-coverage \
		--cover-package notify_send \
		--cover-erase \
		--cover-html \
		--cover-html-dir coverage
