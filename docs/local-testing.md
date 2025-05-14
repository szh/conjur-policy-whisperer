# Local Testing Guide

This guide explains how to test the Conjur Policy Whisperer locally before deploying it to your GitHub Actions workflows.

## Prerequisites

- Docker installed on your local machine
- Access to a Conjur server with JWT authentication configured
- A JWT token for authentication

## Setting Up Local Environment Variables

```bash
# Conjur connection details
export CONJUR_URL=https://your-conjur-url
export CONJUR_ACCOUNT=your-conjur-account

# JWT authentication settings
export CONJUR_JWT_SERVICE_ID=github  # Or whatever service ID you configured in Conjur
export JWT_TOKEN=your-jwt-token      # See below for how to obtain this
```

## Obtaining a JWT Token for Local Testing

When testing locally, you'll need a valid JWT token that matches what Conjur expects. Here are a few options:

### Option 1: Use a GitHub Personal Access Token Fine-grained Token (recommended)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create a new token with repository access to the repo you want to test
3. Grant "Contents" read-only permission
4. Generate the token and use it as your `JWT_TOKEN` environment variable

### Option 2: Generate a Test JWT Token

You can create a test JWT token that mimics the GitHub Actions token format:

```bash
#!/bin/bash

# Install jwt-cli if needed
# npm install -g jwt-cli

# Generate a JWT token that mimics GitHub Actions
jwt sign \
  --secret your-secret \
  --exp "+1h" \
  --aud "https://github.com/your-org" \
  --iss "https://token.actions.githubusercontent.com" \
  --sub "repo:your-org/your-repo:ref:refs/heads/main" \
  --repository "your-org/your-repo"
```

Note: You'll need to configure your Conjur JWT authenticator to accept this token format and validate it with the appropriate key.

## Running the Test Script

Once you have your environment variables set up:

```bash
./test-policy.sh examples/sample-policy.yml root
```

Replace `examples/sample-policy.yml` with the path to your policy file and `root` with the appropriate policy branch.

## Troubleshooting

If you encounter authentication issues, check:

1. Is your JWT token valid and not expired?
2. Does your JWT token contain the claims expected by your Conjur JWT authenticator?
3. Is the `identity-path` correctly configured in Conjur?
4. Does the host identity in Conjur have the necessary permissions?

You can debug JWT authentication issues by looking at the Conjur server logs.
