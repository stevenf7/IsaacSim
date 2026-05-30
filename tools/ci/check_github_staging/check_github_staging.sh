#! /bin/bash

# First we'll go ahead and do the clone in bash because its easier than
# using python.

# Make the destination folder because why not
DEST=${1:-/tmp/isaacsim_staging}
rm -rf "$DEST"
mkdir -p "$DEST"

# Get the repository URL from repo.toml
GITHUB_REPO_URL=$(grep -Po 'github_repo_url = "\K[^"]*' repo.toml | sed 's/env://')

# temp for testing
# GITHUB_REPO_URL="https://oauth2:${GITLAB_PUSH_TOKEN}@gitlab-master.nvidia.com/omniverse/isaac/isaacsim_staging.git"
GITHUB_REPO_URL="https://gitlab-master.nvidia.com/omniverse/isaac/isaacsim_staging.git"


# Scan the branch that stage-to-gitlab just pushed, NOT the pre-merge default
# branch. A plain clone checks out the staging repo default branch (main), i.e.
# the state from the previous update, so newly introduced banned words went
# unseen.
STAGING_BRANCH="upstream/update_from_${CI_COMMIT_SHORT_SHA}"
if [ -n "${CI_COMMIT_SHORT_SHA}" ]; then
    # In CI we MUST scan the freshly pushed staging branch. If it cannot be
    # cloned, fail hard rather than silently regressing to the stale,
    # pre-merge default branch (that would defeat this very check).
    echo "Scanning staging branch: $STAGING_BRANCH"
    if ! git clone -v --progress --depth=1 --branch "$STAGING_BRANCH" "$GITHUB_REPO_URL" "$DEST"; then
        echo "Failed to clone staging branch '$STAGING_BRANCH'; refusing to fall back to the pre-merge default branch."
        exit 1
    fi
else
    # Local manual run without a staging branch: scan the default branch.
    echo "CI_COMMIT_SHORT_SHA unset; scanning default branch."
    if ! git clone -v --progress --depth=1 "$GITHUB_REPO_URL" "$DEST"; then
        echo "Failed to clone the repository"
        exit 1
    fi
fi

# Ensure LFS content is fetched (clone usually handles this via smudge filter,
# but explicit pull guards against misconfigured environments)
git -C "$DEST" lfs pull

# We no longer depend on the 'file' command; the Python script detects text files itself.
echo "Starting banned word check"
python3 tools/ci/check_github_staging/check_github_staging.py "$DEST"

