#!/bin/bash
set -e

# This script helps test the Conjur Policy Whisperer action locally
# before using it in a GitHub workflow

echo "Conjur Policy Whisperer - Local Test Script"
echo "==========================================="
echo

# Check for required environment variables
for VAR in CONJUR_URL CONJUR_ACCOUNT CONJUR_JWT_SERVICE_ID JWT_TOKEN; do
  if [ -z "${!VAR}" ]; then
    echo "Error: $VAR environment variable is not set."
    echo
    echo "Please set the following environment variables:"
    echo "  export CONJUR_URL=https://your-conjur-url"
    echo "  export CONJUR_ACCOUNT=your-conjur-account"
    echo "  export CONJUR_JWT_SERVICE_ID=github"
    echo "  export JWT_TOKEN=your-jwt-token"
    exit 1
  fi
done

# Check for policy file argument
if [ -z "$1" ]; then
  echo "Error: No policy file specified"
  echo
  echo "Usage: $0 path/to/policy.yml [policy-branch]"
  echo
  echo "Example: $0 ./examples/sample-policy.yml root"
  exit 1
fi

POLICY_FILE="$1"
POLICY_BRANCH="${2:-$(basename "$POLICY_FILE" .yml)}"

if [ ! -f "$POLICY_FILE" ]; then
  echo "Error: Policy file '$POLICY_FILE' not found."
  exit 1
fi

echo "Testing policy: $POLICY_FILE"
echo "Using branch: $POLICY_BRANCH"
echo

# Run the policy validation
echo "Running dry-run validation with JWT authentication..."
JWT_TOKEN=$( curl -s -H "Authorization:bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL" | jq -r .value )
# Create a .conjurrc file for the Conjur CLI
cat <<EOF > ".conjurrc"
appliance_url: $CONJUR_URL
account: $CONJUR_ACCOUNT
authn_type: jwt
service_id: $CONJUR_JWT_SERVICE_ID
jwt_file: $JWT_TOKEN
EOF

docker pull cyberark/conjur-cli:latest    
if ! docker run --rm \
      -e CONJURRC="/conjur/.conjurrc" \
      -v "$(pwd):/conjur" \
      cyberark/conjur-cli:latest \
      policy load --dry-run -b "$POLICY_BRANCH" -f "/conjur/$POLICY_FILE" > "$TEMP_OUTPUT" 2>&1; then
  
  echo
  echo "✅ Policy validation successful!"
else
  echo
  echo "❌ Policy validation failed!"
  exit 1
fi
