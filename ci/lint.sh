#!/usr/bin/env bash
set -e
set -o pipefail

echo "--- Running black (formatting)"
black --check .

echo "--- Running flake8 (linting)"
flake8 .
