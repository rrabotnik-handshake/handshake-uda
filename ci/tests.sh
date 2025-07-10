#!/bin/bash
set -euo pipefail

#Capture coverage artifacts
mkdir -p coverage

echo "--- Login to Buf Schema Registry"
current_path=$(dirname "$0")
"${current_path}"/bsr-login.sh

echo "--- Running Python tests with coverage"
pytest --cov=. --cov-report=term --cov-report=xml:tests/coverage.xml
