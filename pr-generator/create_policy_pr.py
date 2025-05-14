#!/usr/bin/env python3
"""
Conjur Policy PR Creator

This script takes a Conjur policy YAML content and creates a Pull Request
to add it to a GitHub repository.
"""

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime

import yaml
from github import Github, GithubException


def create_github_pr(repo_owner, repo_name, policy_content, file_path, branch_name, commit_message, pr_title, pr_description, github_token):
    """Create a PR to the GitHub repository with the policy content"""
    try:
        g = Github(github_token)
        repo = g.get_repo(f"{repo_owner}/{repo_name}")
        
        # Get default branch
        default_branch = repo.default_branch
        default_branch_ref = repo.get_git_ref(f"heads/{default_branch}")
        default_branch_sha = default_branch_ref.object.sha
        
        # Create a new branch
        try:
            repo.create_git_ref(f"refs/heads/{branch_name}", default_branch_sha)
            print(f"Created new branch: {branch_name}")
        except GithubException as e:
            if e.status == 422:  # Branch already exists
                print(f"Branch {branch_name} already exists. Will update it.")
            else:
                raise
        
        # Check if file already exists
        try:
            contents = repo.get_contents(file_path, ref=branch_name)
            
            # File exists, update it
            print(f"Updating existing file: {file_path}")
            result = repo.update_file(
                file_path,
                commit_message,
                policy_content,
                contents.sha,
                branch=branch_name
            )
            commit_sha = result["commit"].sha
        except Exception:
            # File doesn't exist, create it
            print(f"Creating new file: {file_path}")
            result = repo.create_file(
                file_path,
                commit_message,
                policy_content,
                branch=branch_name
            )
            commit_sha = result["commit"].sha
        
        # Create PR if it doesn't exist
        existing_prs = repo.get_pulls(state="open", head=f"{repo_owner}:{branch_name}", base=default_branch)
        
        if existing_prs.totalCount == 0:
            # Create a new PR
            pr = repo.create_pull(
                title=pr_title,
                body=pr_description,
                head=branch_name,
                base=default_branch
            )
            print(f"Created new PR #{pr.number}: {pr.html_url}")
            return pr.html_url
        else:
            pr = existing_prs[0]
            print(f"Using existing PR #{pr.number}: {pr.html_url}")
            return pr.html_url
        
    except Exception as e:
        print(f"Error creating PR: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Create a GitHub PR for a Conjur policy")
    parser.add_argument("--content", help="The policy content as a string")
    parser.add_argument("--file", help="Path to a policy file to read")
    parser.add_argument("--output", help="Path to save the policy content to before creating PR")
    parser.add_argument("--repo-owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo-name", required=True, help="GitHub repository name")
    parser.add_argument("--dest-path", required=True, help="Destination path in the repo (e.g., 'policies/app1.yml')")
    parser.add_argument("--branch", help="Branch name to create (default: policy-update-TIMESTAMP)")
    parser.add_argument("--commit-msg", help="Commit message")
    parser.add_argument("--pr-title", help="PR title")
    parser.add_argument("--pr-description", help="PR description")
    parser.add_argument("--token", help="GitHub token. If not provided, will use GITHUB_TOKEN env var")
    
    args = parser.parse_args()
    
    # Get the policy content
    if args.content:
        policy_content = args.content
    elif args.file:
        try:
            with open(args.file, "r") as f:
                policy_content = f.read()
        except Exception as e:
            print(f"Error reading policy file: {str(e)}")
            return 1
    else:
        parser.error("Either --content or --file is required")
        return 1
        
    # Save policy content to output file if specified
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(policy_content)
                print(f"Policy content saved to {args.output}")
        except Exception as e:
            print(f"Error saving policy content: {str(e)}")
            return 1
    
    
    # Set default values
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_basename = os.path.basename(args.dest_path).split(".")[0]
    
    branch_name = args.branch or f"policy-update-{file_basename}-{timestamp}"
    commit_message = args.commit_msg or f"Add/Update Conjur policy: {args.dest_path}"
    pr_title = args.pr_title or f"Add/Update Conjur policy: {file_basename}"
    pr_description = args.pr_description or (
        f"This PR adds or updates the Conjur policy file at `{args.dest_path}`.\n\n"
        f"Generated by the Conjur Policy PR Creator script at {datetime.now().isoformat()}"
    )
    
    # Get GitHub token
    github_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: No GitHub token provided. Use --token or set GITHUB_TOKEN environment variable.")
        return 1
    
    # Create PR
    try:
        pr_url = create_github_pr(
            args.repo_owner,
            args.repo_name,
            policy_content,
            args.dest_path,
            branch_name,
            commit_message,
            pr_title,
            pr_description,
            github_token
        )
        print(f"Successfully created PR: {pr_url}")
        return 0
    except Exception as e:
        print(f"Failed to create PR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
