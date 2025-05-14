#!/bin/bash
set -ex

# Default policy directory
POLICY_DIR=${POLICY_DIR:-.}

# Get the base commit for comparison
if [ -n "$GITHUB_BASE_REF" ]; then
  # For pull requests
  BASE_COMMIT=$(git merge-base HEAD "origin/$GITHUB_BASE_REF")
else
  # For pushes, use the parent of the current commit
  BASE_COMMIT=$(git rev-parse HEAD^)
fi

# Find all changed .yml or .yaml files in the policy directory
CHANGED_POLICIES=$(git diff --name-only --diff-filter=ACMRT "$BASE_COMMIT" HEAD -- "$POLICY_DIR" | grep -E '\.ya?ml$' || true)

# Set output whether we have policy changes
if [ -z "$CHANGED_POLICIES" ]; then
  echo "::set-output name=has_policy_changes::false"
  echo "No policy file changes detected."
else
  echo "::set-output name=has_policy_changes::true"
  echo "::set-output name=changed_policies::$CHANGED_POLICIES"
  echo "Changed policy files:"
  echo "$CHANGED_POLICIES"
fi
