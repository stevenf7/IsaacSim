#! /bin/bash

# First we'll go ahead and do the clone in bash because its easier than
# using python.

# Make the destination folder because why not
mkdir -p $1

# Get the repository URL from repo.toml
GITHUB_REPO_URL=$(grep -Po 'github_repo_url = "\K[^"]*' repo.toml | sed 's/env://')

# temp for testing
GITHUB_REPO_URL="https://oauth2:${GITLAB_PUSH_TOKEN}@gitlab-master.nvidia.com/omniverse/isaac/isaacsim_staging.git"


# Clone the repository
git clone -v --progress --depth=1 $GITHUB_REPO_URL $1

# Check if the clone was successful
if [ $? -ne 0 ]; then
    echo "Failed to clone the repository"
    exit 1
fi


# We no longer depend on the 'file' command; the Python script detects text files itself.
echo "Starting banned word check"
python3 tools/ci/check_github_staging/check_github_staging.py $1

