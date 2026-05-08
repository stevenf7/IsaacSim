#!/bin/bash

: "${PLATFORM_TAG:=x86_64}"
# Starting container

# Constants to make things a bit more readable, hopefully
GITLAB_BASE="gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim"
NGC_BASE="nvcr.io/nvidian/isaac-sim"

BASE_CONTAINER="${GITLAB_BASE}-cicd:pipeline-${CI_PIPELINE_ID}-${PLATFORM_TAG}"

# Destination tags
if [ "$CI_PIPELINE_SOURCE" == "merge_request_event" ]; then
    # For an MR just tag it with isaac-sim-mr:latest-branch-platform and isaac-sim-mr:branch-hash-platform
    CONTAINER_TAGS="${GITLAB_BASE}-mr:latest-${CI_COMMIT_REF_SLUG}-${PLATFORM_TAG}"
    CONTAINER_TAGS="${CONTAINER_TAGS},${GITLAB_BASE}-mr:${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}-${PLATFORM_TAG}"
else
    # For non-MRs tag it with isaac-sim:latest-branch-platform and isaac-sim:branch-hash-platform
    CONTAINER_TAGS="${GITLAB_BASE}:latest-${CI_COMMIT_REF_SLUG}-${PLATFORM_TAG}"
    CONTAINER_TAGS="${CONTAINER_TAGS},${GITLAB_BASE}:${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}-${PLATFORM_TAG}"
    if [ "${CI_COMMIT_REF_PROTECTED:-false}" = "true" ]; then
        # Additionally protected non-MRs get pushed to NGC as isaac-sim:latest-branch-platform and latest-branch-hash-platform
        CONTAINER_TAGS="${CONTAINER_TAGS},${NGC_BASE}:latest-${CI_COMMIT_REF_SLUG}-${PLATFORM_TAG}"
        CONTAINER_TAGS="${CONTAINER_TAGS},${NGC_BASE}:latest-${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}-${PLATFORM_TAG}"
    else
        echo "Skipping NGC tags for unprotected ref ${CI_COMMIT_REF_NAME:-unknown}"
    fi
fi

echo "Base container: $BASE_CONTAINER"
echo "Container tags to process: $CONTAINER_TAGS"

# Initialize counters for summary
total_tags=0
successful_tags=0
successful_pushes=0

# Set IFS to comma for splitting
OLD_IFS="$IFS"
IFS=','

# Iterate through comma-separated list
for tag in $CONTAINER_TAGS; do
    # Trim whitespace from tag
    tag=$(echo "$tag" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    if [ -n "$tag" ]; then
        total_tags=$((total_tags + 1))
        target_tag="${tag}"

        echo "Processing tag: $tag"
        echo "Tagging: $BASE_CONTAINER -> $target_tag"

        if docker tag "$BASE_CONTAINER" "$target_tag"; then
            echo "Successfully tagged: $target_tag"
            successful_tags=$((successful_tags + 1))

            echo "Pushing: $target_tag"
            if docker push "$target_tag"; then
                echo "Successfully pushed: $target_tag"
                successful_pushes=$((successful_pushes + 1))
            else
                echo "ERROR: Failed to push: $target_tag"
            fi
        else
            echo "ERROR: Failed to tag: $target_tag"
        fi
        echo "---"
    fi
done

# Restore original IFS
IFS="$OLD_IFS"

echo "=== SUMMARY ==="
echo "Total tags processed: $total_tags"
echo "Successful tags: $successful_tags"
echo "Successful pushes: $successful_pushes"

if [ "$successful_pushes" -eq "$total_tags" ]; then
    echo "✅ All operations completed successfully!"
    exit 0
else
    failed_ops=$((total_tags - successful_pushes))
    echo "⚠️  $failed_ops operation(s) failed. Check the output above for details."
    exit 1
fi
