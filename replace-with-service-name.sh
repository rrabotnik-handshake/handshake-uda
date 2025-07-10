#!/bin/bash
set -euo pipefail

echo "--- Replacing REPLACE_WITH_SERVICE_NAME with $1"
grep -lR --exclude $0 REPLACE_WITH_SERVICE_NAME . | xargs -n 1 sed -i "" "s/REPLACE_WITH_SERVICE_NAME/$1/g"
