"""
Templates and examples handling for Policy Whisperer
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any

from policy_whisperer.utils import load_policy_structure

logger = logging.getLogger(__name__)

# Policy templates repository URL
POLICY_REPO_BASE_URL = "https://raw.githubusercontent.com/infamousjoeg/conjur-policies/master"

# Cache for policy templates
policy_templates_cache = {}

# Load the policy structure
POLICY_STRUCTURE = load_policy_structure()

# Predefined policy templates for offline use when GitHub templates are not available
PREDEFINED_TEMPLATES = {
    "authn/authn-jwt-github": """
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
    
    - !variable
      id: issuer
    
    - !group hosts
    
    - !permit
      role: !group hosts
      privilege: [ read, authenticate ]
      resource: !webservice
    """,
    
    "authn/oidc/azure": """
- !policy
  id: conjur/authn-oidc/azure
  body:
    - !webservice
      
    - !variable
      id: provider-uri
    
    - !variable
      id: client-id
      
    - !variable
      id: client-secret
    
    - !group hosts
    
    - !permit
      role: !group hosts
      privilege: [ read, authenticate ]
      resource: !webservice
    """,
    
    "cloud/aws/aws": """
- !policy
  id: aws
  body:
    - !group admins
    
    - !variable
      id: access_key_id
      annotations:
        description: AWS Access Key ID
    
    - !variable
      id: secret_access_key
      annotations:
        description: AWS Secret Access Key

    - !variable
      id: region
      annotations:
        description: AWS Region
    """,
    
    "ci/github/actions": """
- !policy
  id: github-actions
  owner: !group admins
  annotations:
    description: GitHub Actions resources and secret variables
  body:
    # Group of hosts that can authenticate using this JWT Authenticator
    - !group
      annotations:
        description: Group of GitHub Actions hosts that can authenticate
    
    # Collection of hosts that can authenticate
    - &hosts
      - !host
        id: repo-my-org-my-repo
        annotations:
          description: GitHub Actions for my-org/my-repo
          authn-jwt/github/repository: my-org/my-repo
          authn-jwt/github/workflow_ref: refs/heads/main
          authn-jwt/github/repository_owner: org-name
    
    # Grant all hosts in collection above to be members of github-actions group
    - !grant
      role: !group
      members: *hosts
    """
}

def get_template_path(policy_type: str, template_name: str) -> Optional[str]:
    """
    Get the correct path for a template based on the policy structure
    """
    try:
        # Handle simple policy types that are direct keys in the structure
        if isinstance(POLICY_STRUCTURE.get(policy_type, []), list):
            for filename in POLICY_STRUCTURE.get(policy_type, []):
                if filename.startswith(f"{template_name}.") or template_name in filename:
                    return f"{policy_type}/{filename}"
        
        # Handle nested policy types
        elif isinstance(POLICY_STRUCTURE.get(policy_type, {}), dict):
            for subdir, files in POLICY_STRUCTURE.get(policy_type, {}).items():
                for filename in files:
                    if filename.startswith(f"{template_name}.") or template_name in filename:
                        return f"{policy_type}/{subdir}/{filename}"
    
    except Exception as e:
        logger.error(f"Error getting template path: {e}")
    
    return None

def fetch_policy_template(policy_type: str, template_name: str) -> Optional[str]:
    """
    Fetch a policy template from the repository or cache
    """
    cache_key = f"{policy_type}/{template_name}"
    
    # Check if we have this template in cache
    if cache_key in policy_templates_cache:
        logger.info(f"Using cached template for {cache_key}")
        return policy_templates_cache[cache_key]
    
    try:
        # Get the template path
        template_path = get_template_path(policy_type, template_name)
        
        if not template_path:
            logger.warning(f"Template path not found for {policy_type}/{template_name}")
            return None
        
        # Construct the URL
        url = f"{POLICY_REPO_BASE_URL}/{template_path}"
        
        logger.info(f"Fetching template from {url}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            template_content = response.text
            # Cache the template
            policy_templates_cache[cache_key] = template_content
            return template_content
        else:
            logger.warning(f"Failed to fetch template {url}: {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Error fetching template {policy_type}/{template_name}: {e}")
        return None

def get_policy_types() -> List[str]:
    """
    Returns a list of available policy types
    """
    return list(POLICY_STRUCTURE.keys())

def get_template_examples() -> Dict[str, List[str]]:
    """
    Returns examples of templates for each policy type
    """
    examples = {}
    
    for policy_type, value in POLICY_STRUCTURE.items():
        if isinstance(value, list):
            # For simple policy types with a list of templates
            examples[policy_type] = [os.path.splitext(filename)[0] for filename in value[:2]]  # Limit to 2 examples
        elif isinstance(value, dict):
            # For nested policy types
            examples[policy_type] = []
            for subdir, files in value.items():
                if files:
                    # Add the first template from each subdirectory
                    examples[policy_type].append(f"{subdir}/{os.path.splitext(files[0])[0]}")
    
    return examples
