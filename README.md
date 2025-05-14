# Conjur Policy Whisperer

A GitHub Action that validates Conjur policy files in pull requests and provides detailed feedback.

> **Note**: This action uses JWT authentication to securely connect to your Conjur server without storing API keys.
>
> See [JWT Migration Guide](docs/jwt-migration.md) and [Local Testing Guide](docs/local-testing.md) for more information.

## Features

- Automatically detects changes to YAML policy files in PRs
- Performs dry-run validation of policies against a Conjur server
- Comments on PRs with validation results
- Updates comments when PR content changes
- Blocks PRs from being merged if policy validation fails
- Works with any repository containing Conjur policy files

## Usage

Add the following to your repository's workflow file (e.g., `.github/workflows/conjur-policy-validation.yml`):

### Prerequisites

Before using this action, you need to set up JWT authentication in your Conjur instance:

1. Configure the JWT Authenticator in Conjur for GitHub Actions:
   ```bash
   conjur policy load -b root -f jwt-authenticator-policy.yml
   ```
   
   Example JWT authenticator policy:
   ```yaml
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
   ```

2. Configure the JWT Authenticator variables:
   ```bash
   # Set the JWKS URI for GitHub Actions
   conjur variable set -i conjur/authn-jwt/github/jwks-uri -v "https://token.actions.githubusercontent.com/.well-known/jwks"
   
   # Configure which claim to use for identity (typically sub)
   conjur variable set -i conjur/authn-jwt/github/token-app-property -v "repository"
   
   # Set the Conjur path where identities are stored
   conjur variable set -i conjur/authn-jwt/github/identity-path -v "github-actions"
   ```

3. Create a host for your repository in Conjur:
   ```yaml
   - !policy
     id: github-actions
     body:
     - !host
       id: org-name/repo-name
       annotations:
         repository: org-name/repo-name
   
     # Grant this host permission to validate policies
     - !grant
       role: !group conjur/authn-jwt/github/apps
       member: !host org-name/repo-name
   ```

```yaml
name: Validate Conjur Policies

on:
  pull_request:
    paths:
      - '**.yml'
      - '**.yaml'

jobs:
  validate-policies:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Validate Conjur Policies
        uses: your-org/conjur-policy-whisperer@v1
        with:
          conjur_url: ${{ secrets.CONJUR_URL }}
          conjur_account: ${{ secrets.CONJUR_ACCOUNT }}
          conjur_jwt_service_id: ${{ secrets.CONJUR_JWT_SERVICE_ID }}
          policy_dir: './path/to/policies'  # Optional, defaults to repository root
```

## Configuration

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `conjur_url` | URL of Conjur | Yes | - |
| `conjur_account` | Conjur account name | Yes | - |
| `conjur_jwt_service_id` | Conjur JWT Authenticator service ID | Yes | - |
| `policy_dir` | Directory containing policy files | No | `.` (repository root) |
| `github_token` | GitHub token for PR comments and JWT authentication | No | `${{ github.token }}` |

## Security Considerations

- Store your Conjur configuration as GitHub secrets
- Configure the JWT authenticator in Conjur with appropriate claims and constraints
- Set up proper identity scope and audience in the JWT Authenticator configuration
- Use Conjur's RBAC to restrict what the authenticated identity can access
- Ensure the JWT Service ID has only the permissions needed for policy validation

## Example PR Comment

When a PR contains Conjur policy file changes, the action will comment with validation results:

```
# Conjur Policy Validation Results

**Last Updated:** 2025-05-14 10:15:32 UTC

## ✅ All policies validated successfully

## ✅ Policy validation succeeded for: policies/app-secrets.yml

```
{detailed validation output}
```
```

If validation fails, the PR will be blocked from merging:

```
# Conjur Policy Validation Results

**Last Updated:** 2025-05-14 10:20:45 UTC

## ❌ Policy validation failed - This PR cannot be merged

## ❌ Policy validation failed for: policies/app-secrets.yml

```
{error details}
```
```

## License

MIT
