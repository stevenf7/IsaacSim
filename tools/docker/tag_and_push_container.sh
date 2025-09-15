#!/bin/sh

: "${PLATFORM_TAG:=x86_64}"
# Starting container
BASE_CONTAINER="nvcr.io/nvidian/isaac-sim:latest-${CI_COMMIT_REF_SLUG}-${PLATFORM_TAG}"
# Destination tags
CONTAINER_TAGS="gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-${CI_COMMIT_REF_SLUG}-${PLATFORM_TAG},nvcr.io/nvidian/isaac-sim:latest-${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}-${PLATFORM_TAG}"


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
