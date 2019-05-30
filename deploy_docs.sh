#!/bin/bash
set -e
conda install -c conda-forge doctr --yes
doctr deploy . --built-docs docs/_build/html
