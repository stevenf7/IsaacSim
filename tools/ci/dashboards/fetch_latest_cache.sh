#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# Hydrate a dashboard cache directory from the most recent successful artifact
# of a given GitLab job, fetched via the API.  Used by the historical-data
# jobs as an "evergreen" baseline so a pipeline whose upstream was skipped or
# whose own runner has no cache key still gets a starting point.
#
# Always exits 0: a missing artifact (first run, expired, network blip) must
# not fail the calling job — it just means the cache stays empty and the job
# fetches everything from scratch.
#
# Usage:
#   fetch_latest_cache.sh \
#     --project "${CI_PROJECT_PATH}" \
#     --job    get-isaac-lab-historical-data \
#     --ref    "${CI_DEFAULT_BRANCH:-develop}" \
#     --dest   .
#
# `--ref` defaults to ${CI_DEFAULT_BRANCH:-develop} so MR pipelines hydrate
# from the default branch's last good run, not the MR's own (likely empty)
# pipeline history.

set -uo pipefail

PROJECT=""
JOB=""
REF=""
DEST="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --job)     JOB="$2";     shift 2 ;;
    --ref)     REF="$2";     shift 2 ;;
    --dest)    DEST="$2";    shift 2 ;;
    *) echo "fetch_latest_cache: unknown arg '$1' — skipping." >&2; exit 0 ;;
  esac
done

REF="${REF:-${CI_DEFAULT_BRANCH:-develop}}"
API="${CI_API_V4_URL:-https://gitlab-master.nvidia.com/api/v4}"

# Resolve token, recording WHICH variable supplied it.  Operators chasing
# auth failures should not have to guess; the value is never logged.
TOKEN=""
TOKEN_SOURCE=""
for var in GITLAB_AUTH_TOKEN GITLAB_TOKEN GITLAB_API_TOKEN; do
  val="${!var:-}"
  if [[ -n "$val" ]]; then
    TOKEN="$val"
    TOKEN_SOURCE="$var"
    break
  fi
done

if [[ -z "$TOKEN" || -z "$PROJECT" || -z "$JOB" ]]; then
  echo "fetch_latest_cache: missing token, project, or job — skipping seed." >&2
  exit 0
fi
echo "fetch_latest_cache: using token from \$$TOKEN_SOURCE." >&2

# URL-encode path segments and the JOB query value.  Project paths and refs
# typically only contain '/'; JOB names are normally [A-Za-z0-9_-] but we
# encode the small set of chars that would corrupt the URL anyway, since
# this script accepts arbitrary --job input.
url_encode_segment() {
  local s="$1"
  s="${s//%/%25}"   # MUST be first
  s="${s//\//%2F}"
  printf '%s' "$s"
}
url_encode_query() {
  local s="$1"
  s="${s//%/%25}"   # MUST be first
  s="${s//&/%26}"
  s="${s//=/%3D}"
  s="${s//+/%2B}"
  s="${s//#/%23}"
  s="${s// /%20}"
  printf '%s' "$s"
}
PROJECT_ENC="$(url_encode_segment "$PROJECT")"
REF_ENC="$(url_encode_segment "$REF")"
JOB_ENC="$(url_encode_query "$JOB")"
URL="${API}/projects/${PROJECT_ENC}/jobs/artifacts/${REF_ENC}/download?job=${JOB_ENC}"

mkdir -p "$DEST"
TMP="$(mktemp --tmpdir=/tmp fetch_latest_cache.XXXXXX.zip)" || {
  echo "fetch_latest_cache: mktemp failed — skipping seed." >&2
  exit 0
}
trap 'rm -f "$TMP"' EXIT

# 500 MiB cap on the artifact body — real caches sit under 100 MiB; anything
# larger is a runaway and would risk filling the runner's ephemeral disk.
MAX_BYTES=524288000

echo "fetch_latest_cache: GET $URL" >&2
HTTP_CODE="$(curl -sSL -w '%{http_code}' -o "$TMP" \
  --header "PRIVATE-TOKEN: ${TOKEN}" \
  --max-time 120 \
  --max-filesize "$MAX_BYTES" \
  "$URL")" || HTTP_CODE="000"

case "$HTTP_CODE" in
  200)
    if unzip -oq "$TMP" -d "$DEST"; then
      echo "fetch_latest_cache: hydrated '$DEST' from latest successful '$JOB' on '$REF'." >&2
    else
      echo "fetch_latest_cache: artifact downloaded but unzip failed — seed skipped." >&2
    fi
    ;;
  404)
    echo "fetch_latest_cache: no successful artifact yet for '$JOB' on '$REF' (HTTP 404) — first-run seed skipped." >&2
    ;;
  *)
    echo "fetch_latest_cache: unexpected HTTP ${HTTP_CODE} — seed skipped." >&2
    ;;
esac
exit 0
