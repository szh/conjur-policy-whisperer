# Conjur Policy PR Creator

This tool allows you to create a GitHub Pull Request to add or update a Conjur policy file in a repository.

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make the script executable:

```bash
chmod +x create_policy_pr.py
```

## Usage

You can use this script in two ways:

### 1. Provide the policy content directly:

```bash
./create_policy_pr.py \
  --content '- !policy\n  id: app1\n  body:\n    - !group admins' \
  --repo-owner szh \
  --repo-name conjur-policy-whisperer-demo \
  --dest-path policies/whisper/app1.yml \
  --token ghp_yourtoken123456
```

### 2. Read policy from a file:

```bash
./create_policy_pr.py \
  --file path/to/local-policy-file.yml \
  --repo-owner your-org \
  --repo-name your-repo \
  --dest-path policies/app1.yml \
  --token YOUR_GITHUB_TOKEN
```

## Options

```
--content TEXT          The policy content as a string
--file TEXT             Path to a policy file to read
--output TEXT           Path to save the policy content to before creating PR
--repo-owner TEXT       GitHub repository owner [required]
--repo-name TEXT        GitHub repository name [required]
--dest-path TEXT        Destination path in the repo (e.g., 'policies/app1.yml') [required]
--branch TEXT           Branch name to create (default: policy-update-TIMESTAMP)
--commit-msg TEXT       Commit message
--pr-title TEXT         PR title
--pr-description TEXT   PR description
--token TEXT            GitHub token. If not provided, will use GITHUB_TOKEN env var
```

## Environment Variables

- `GITHUB_TOKEN`: GitHub token for authentication (can be used instead of --token)

## Examples

### Basic usage with minimal parameters:

```bash
export GITHUB_TOKEN=ghp_yourtoken123456

./create_policy_pr.py \
  --file ../examples/sample-policy.yml \
  --repo-owner szh \
  --repo-name conjur-policy-whisperer-demo \
  --dest-path policies/whisper/app1.yml
```

### Advanced usage with custom PR details:

```bash
./create_policy_pr.py \
  --file my-policy.yml \
  --repo-owner my-org \
  --repo-name conjur-policies \
  --dest-path policies/app1.yml \
  --branch feature/new-app1-policy \
  --commit-msg "Add new policy for App1" \
  --pr-title "New policy for App1" \
  --pr-description "This PR adds a new policy for App1 with the necessary groups and permissions" \
  --token ghp_yourtoken123456
```
