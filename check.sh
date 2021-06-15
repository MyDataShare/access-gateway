#!/usr/bin/env sh

CUR_DIR=`pwd`
TOP_DIR=`dirname $0`
SOURCE_DIR=agw

cd $TOP_DIR

printf "\n===============[ flake8 ]===============\n"
flake8 $SOURCE_DIR
flake8_rc=$?

printf "\n===============[  mypy  ]===============\n"
mypy
mypy_rc=$?

printf "\n===============[ bandit ]===============\n"
bandit -r $SOURCE_DIR
bandit_rc=$?

printf "\n===============[ safety ]===============\n"
safety check --full-report
safety_rc=$?

printf "\n===============[ pytest ]===============\n"
coverage run --branch -m pytest -rxXs
pytest_rc=$?

printf "\n===============[ coverage ]===============\n"
coverage report -m
report_rc=$?
coverage html
html_rc=$?

cd $CUR_DIR

# TODO: Fail on mypy errors
if  [ "$flake8_rc" -ne 0 ] || \
    [ "$mypy_rc" -ne 0 ] || \
    [ "$bandit_rc" -ne 0 ] || \
    [ "$safety_rc" -ne 0 ] || \
    [ "$pytest_rc" -ne 0 ] || \
    [ "$report_rc" -ne 0 ] || \
    [ "$html_rc" -ne 0 ] ;
then
    exit 1
fi
