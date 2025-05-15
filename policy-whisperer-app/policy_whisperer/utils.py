"""
Utility functions for Policy Whisperer
"""

import os
import yaml
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('policy_generator.log')
    ]
)
logger = logging.getLogger(__name__)

# Enable detailed debug logging for LangChain
logging.getLogger('langchain').setLevel(logging.DEBUG)
logging.getLogger('langchain_openai').setLevel(logging.DEBUG)

# Create a custom YAML loader that ignores Conjur-specific tags
class ConjurPolicyLoader(yaml.SafeLoader):
    pass

# Add constructors for all Conjur policy tags
def conjur_tag_constructor(loader, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)

# Register all common Conjur policy tags
for tag in ['policy', 'user', 'host', 'group', 'variable', 'grant', 'permit', 'webservice']:
    yaml.add_constructor(f'!{tag}', conjur_tag_constructor, ConjurPolicyLoader)

def load_policy_structure() -> Dict:
    """
    Load the policy structure from the JSON file
    """
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        policy_structure_path = os.path.join(current_dir, 'policy_structure.json')
        
        logger.info(f"Loading policy structure from: {policy_structure_path}")
        with open(policy_structure_path, 'r') as f:
            structure = json.load(f)
            logger.info(f"Successfully loaded policy structure with {len(structure)} top-level categories")
            return structure
    except Exception as e:
        logger.error(f"Error loading policy structure: {e}")
        logger.exception("Exception details:")
        # Return a minimal structure if the file can't be loaded
        return {
            "authn": ["authn-jwt-github.yml"],
            "ci": {"github": ["actions.yml"]},
            "cloud": {"aws": ["aws.yml"]},
            "web": ["conjur-oidc-demo.yml"]
        }

def analyze_policy_resources(policy: str) -> Dict[str, int]:
    """
    Analyze a policy to count the different types of resources it contains
    """
    resource_counts = {
        "policy": 0,
        "user": 0,
        "host": 0,
        "group": 0,
        "variable": 0,
        "grant": 0,
        "permit": 0,
        "webservice": 0
    }
    
    try:
        lines = policy.split('\n')
        for line in lines:
            line = line.strip()
            for resource_type in resource_counts.keys():
                if f"!{resource_type}" in line:
                    resource_counts[resource_type] += 1
    except Exception as e:
        logger.error(f"Error analyzing policy resources: {e}")
    
    return resource_counts
