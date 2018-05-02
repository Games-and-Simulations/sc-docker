#!/usr/bin/env bash
set -eu

pushd unittests/
nosetests -vv
popd

pushd integration/
ls *.bats | xargs bats -p
popd
