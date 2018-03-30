#!/usr/bin/env bash

pushd integration/
ls *.bats | xargs bats -p
popd
