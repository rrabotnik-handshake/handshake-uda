#!/bin/bash
set -euo pipefail

echo "--- Login to Buf Schema Registry"
current_path=$(dirname "$0")
"${current_path}"/bsr-login.sh

echo "--- Building production image"
docker build \
  -f ci/Dockerfile \
  --ssh=default \
  --secret=id=bsr,src="${HOME}"/.netrc \
  --tag "us-central1-docker.pkg.dev/handshake-artifacts/REPLACE_WITH_SERVICE_NAME/REPLACE_WITH_SERVICE_NAME:latest" \
  --tag "us-central1-docker.pkg.dev/handshake-artifacts/REPLACE_WITH_SERVICE_NAME/REPLACE_WITH_SERVICE_NAME:$BUILDKITE_COMMIT" \
  .

echo "Production image built"

if [ "$BRANCH_SLUG" == "main" ]; then
  docker push "us-central1-docker.pkg.dev/handshake-artifacts/REPLACE_WITH_SERVICE_NAME/REPLACE_WITH_SERVICE_NAME:$BUILDKITE_COMMIT"
  docker push us-central1-docker.pkg.dev/handshake-artifacts/REPLACE_WITH_SERVICE_NAME/REPLACE_WITH_SERVICE_NAME:latest
fi
