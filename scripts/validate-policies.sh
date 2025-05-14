#!/bin/bash
set -e

# Check required environment variables
if [ -z "$CONJUR_URL" ] || [ -z "$CONJUR_ACCOUNT" ] || [ -z "$CONJUR_JWT_SERVICE_ID" ] || [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: Missing required Conjur configuration."
  echo "::set-output name=validation_success::false"
  echo "::set-output name=validation_result::error"
  echo "::set-output name=validation_output::Missing required Conjur configuration."
  exit 1
fi

# Set default values
RESULT_FILE="/tmp/conjur_validation_result.txt"
SUCCESS_FILE="/tmp/conjur_validation_success.txt"
OUTPUT_FILE="/tmp/conjur_validation_output.txt"
TEMP_DIR="/tmp/conjur_policy_validation"

echo "true" > "$SUCCESS_FILE"  # Start assuming success
echo "success" > "$RESULT_FILE"  # Start assuming success
echo "" > "$OUTPUT_FILE"  # Start with empty output

mkdir -p "$TEMP_DIR"

# Process each changed policy file
IFS=$'\n'
for POLICY_FILE in $CHANGED_POLICIES; do
  echo "Validating policy: $POLICY_FILE"
  
  # Extract policy branch name from file path
  POLICY_BRANCH=$(basename "$POLICY_FILE" .yml)
  POLICY_BRANCH=${POLICY_BRANCH%.yaml}  # Also handle yaml extension
  
  # Create temporary file for validation result
  TEMP_OUTPUT="$TEMP_DIR/$(basename "$POLICY_FILE").out"
  
  # Generate JWT token for GitHub Actions
  JWT_TOKEN="$GITHUB_TOKEN"
  
  # Run the policy validation using the Conjur CLI in Docker with JWT authentication
  JWT_TOKEN=$( curl -s -H "Authorization:bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL" | jq -r .value )
  if ! docker run --rm \
      -e CONJUR_APPLIANCE_URL="$CONJUR_URL" \
      -e CONJUR_ACCOUNT="$CONJUR_ACCOUNT" \
      -e CONJUR_AUTHN_JWT_SERVICE_ID="$CONJUR_JWT_SERVICE_ID" \
      -e CONJUR_AUTHN_TOKEN="$JWT_TOKEN" \
      -v "$(pwd):/conjur" \
      cyberark/conjur-cli:latest \
      policy load --dry-run -b "$POLICY_BRANCH" -f "/conjur/$POLICY_FILE" > "$TEMP_OUTPUT" 2>&1; then
    
    # Policy validation failed
    echo "false" > "$SUCCESS_FILE"
    echo "failure" > "$RESULT_FILE"
    echo -e "\n## ❌ Policy validation failed for: $POLICY_FILE\n\n\`\`\`\n$(cat "$TEMP_OUTPUT")\n\`\`\`" >> "$OUTPUT_FILE"
  else
    # Policy validation succeeded
    echo -e "\n## ✅ Policy validation succeeded for: $POLICY_FILE\n\n\`\`\`\n$(cat "$TEMP_OUTPUT")\n\`\`\`" >> "$OUTPUT_FILE"
  fi
done

# Set outputs for GitHub Actions
echo "::set-output name=validation_success::$(cat "$SUCCESS_FILE")"
echo "::set-output name=validation_result::$(cat "$RESULT_FILE")"
ESCAPED_OUTPUT=$(cat "$OUTPUT_FILE" | awk '{printf "%s\\n", $0}')
echo "::set-output name=validation_output::$ESCAPED_OUTPUT"

if [ "$(cat "$SUCCESS_FILE")" == "false" ]; then
  echo "Policy validation encountered errors. PR should be blocked."
else
  echo "All policy validations succeeded."
fi
