#!/usr/bin/env bash

set -e

rm -rf build
rm -rf dist
rm -rf *.egg-info

python -m build
twine upload dist/*
