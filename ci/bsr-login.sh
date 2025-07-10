#!/usr/bin/env bash

set -euo pipefail

# Avoid clashing with existing BSR credentials, can run in local and CI
if ! test -e "${HOME}/.netrc" || ! grep -Fxq "machine joinhandshake.buf.dev" "${HOME}"/.netrc; then
  printf "\nmachine joinhandshake.buf.dev\n\tlogin %s\n\tpassword %s\n" "${BUF_USER}" "${BUF_TOKEN}" >> "${HOME}"/.netrc
fi