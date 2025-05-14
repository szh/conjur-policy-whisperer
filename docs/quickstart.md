# Quick Start Guide - JWT Authentication with Conjur

This guide provides step-by-step instructions for setting up the Conjur Policy Whisperer action with JWT authentication in a new repository.

## 1. Configure JWT Authenticator in Conjur

First, you need to set up JWT authentication in your Conjur instance. The following commands should be run by a Conjur admin:

```bash
# Create a policy file named jwt-auth.yml
cat <<EOF > jwt-auth.yml
- !policy
  id: conjur/authn-jwt/github
  body:
  - !webservice

  - !variable
    id: jwks-uri
  
  - !variable
    id: token-app-property
  
  - !variable
    id: identity-path
  
  - !group
    id: apps
    
  - !permit
    role: !group apps
    privilege: [ read, authenticate ]
    resource: !webservice
EOF

# Load the policy
conjur policy load -b root -f jwt-auth.yml

# Configure the JWT authenticator
conjur variable set -i conjur/authn-jwt/github/jwks-uri -v "https://token.actions.githubusercontent.com/.well-known/jwks"
conjur variable set -i conjur/authn-jwt/github/token-app-property -v "repository"
conjur variable set -i conjur/authn-jwt/github/identity-path -v "github-actions"

# Create a policy for your repository
cat <<EOF > repo-identity.yml
- !policy
  id: github-actions
  body:
  - !host
    id: your-org/your-repo
    annotations:
      repository: your-org/your-repo
  
  # Grant this host permission to authenticate
  - !grant
    role: !group conjur/authn-jwt/github/apps
    member: !host your-org/your-repo
EOF

# Load the repository identity policy
conjur policy load -b root -f repo-identity.yml

# Enable the JWT authenticator
conjur authenticator enable --id authn-jwt/github
```

## 2. Add GitHub Workflow to Your Repository

Create a workflow file at `.github/workflows/validate-conjur-policies.yml`:

```yaml
name: Validate Conjur Policies

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - '**.yml'
      - '**.yaml'

jobs:
  validate-conjur-policies:
    name: Validate Conjur Policies
    runs-on: ubuntu-latest
    
    # Set the permissions needed for OIDC authentication
    permissions:
      id-token: write
      contents: read
      pull-requests: write
      
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Required to detect changes between branches

      - name: Validate Conjur Policy Files
        uses: szh/conjur-policy-whisperer@v1
        with:
          conjur_url: ${{ secrets.CONJUR_URL }}
          conjur_account: ${{ secrets.CONJUR_ACCOUNT }}
          conjur_jwt_service_id: github
          policy_dir: './policies'  # Adjust to your policy directory
```

## 3. Add Repository Secrets

In your GitHub repository:

1. Go to Settings > Secrets and variables > Actions
2. Add the following secrets:
   - `CONJUR_URL`: URL of your Conjur (e.g., `https://conjur.example.com`)
   - `CONJUR_ACCOUNT`: Your Conjur account name

## 4. Test the Integration

1. Create a branch in your repository
2. Add or modify a Conjur policy YAML file
3. Create a pull request
4. The GitHub Action will run automatically, validating your policy and adding comments to the PR

## Troubleshooting

If you encounter issues:

1. Check your Conjur server logs for authentication errors
2. Verify that the JWT authenticator is properly configured
3. Ensure the GitHub Actions workflow has the correct permissions
4. Confirm that your repository name matches exactly what's configured in Conjur

For more details, see the [JWT Migration Guide](jwt-migration.md) and [Local Testing Guide](local-testing.md).
