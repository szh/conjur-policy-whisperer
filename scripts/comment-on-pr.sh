#!/bin/bash
set -e

# Check if we're in a PR context
if [ -z "$GITHUB_EVENT_PATH" ]; then
  echo "Not in a GitHub Actions context. Skipping PR comment."
  exit 0
fi

# Extract PR number
PR_NUMBER=$(jq -r ".pull_request.number // empty" "$GITHUB_EVENT_PATH")
if [ -z "$PR_NUMBER" ]; then
  echo "Not in a pull request context. Skipping PR comment."
  exit 0
fi

# Prepare the comment content
COMMENT_MARKER="<!-- conjur-policy-validator -->"
TIMESTAMP=$(date -u "+%Y-%m-%d %H:%M:%S UTC")
HEADER="# Conjur Policy Validation Results\n\n$COMMENT_MARKER\n\n**Last Updated:** $TIMESTAMP"

if [ "$VALIDATION_SUCCESS" == "true" ]; then
  STATUS="## ✅ All policies validated successfully"
else
  STATUS="## ❌ Policy validation failed - This PR cannot be merged"
fi

COMMENT_BODY="$HEADER\n\n$STATUS\n\n${VALIDATION_OUTPUT//\"/\\\"}"

# Check for existing comment
COMMENTS_URL="https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments"
COMMENT_ID=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "$COMMENTS_URL" | jq ".[] | select(.body | contains(\"$COMMENT_MARKER\")) | .id")

if [ -n "$COMMENT_ID" ]; then
  # Update existing comment
  curl -s -X PATCH \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -d "{\"body\":\"$COMMENT_BODY\"}" \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/comments/$COMMENT_ID"
  
  echo "Updated existing comment on PR #$PR_NUMBER"
else
  # Create new comment
  curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -d "{\"body\":\"$COMMENT_BODY\"}" \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments"
  
  echo "Created new comment on PR #$PR_NUMBER"
fi

# If validation failed, exit with error code to fail the GitHub action
if [ "$VALIDATION_SUCCESS" != "true" ]; then
  echo "Policy validation failed. Exiting with error."
  exit 1
fi
