#!/bin/bash
# Batch process: add CODEOWNERS to all repos in an org

REPOS=(
    "org/repo-alpha"
    "org/repo-beta"
    "org/repo-gamma"
    "org/repo-delta"
)

TASK="Create a CODEOWNERS file that assigns reviews to the maintainers team"

for repo in "${REPOS[@]}"; do
    echo "=== Processing $repo ==="

    # Clone the repo
    gh repo clone "$repo" "/tmp/batch-$repo"
    cd "/tmp/batch-$repo" || exit 1

    # Run OpenHands
    if openhands --headless --override-with-envs -t "$TASK"; then
        # Commit and create PR if changes were made
        if ! git diff --quiet; then
            git checkout -b openhands/add-codeowners
            git add CODEOWNERS
            git commit -m "Add CODEOWNERS file"
            git push origin openhands/add-codeowners
            gh pr create --title "Add CODEOWNERS" \
                --body "Automated by OpenHands batch processor"
            echo "  -> PR created for $repo"
        else
            echo "  -> No changes needed for $repo"
        fi
    else
        echo "  -> FAILED for $repo — check logs"
    fi

    cd -
done

echo "Batch processing complete"