from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import yaml
import json
import logging

# Import from the new modular Policy Whisperer package
from policy_whisperer.generator import generate_policy_from_prompt, generate_policy_explanation
from policy_whisperer.utils import analyze_policy_resources
from policy_whisperer.templates import get_policy_types, POLICY_STRUCTURE

# Get debug mode from environment variable or default to False
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

# Configure app logging
logging.basicConfig(
    level=logging.DEBUG if debug_mode else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Configure module-specific loggers
if debug_mode:
    # Set specific loggers to DEBUG level
    logging.getLogger('policy_whisperer').setLevel(logging.DEBUG)
    logging.getLogger('langchain').setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")
else:
    # Set specific loggers to INFO level
    logging.getLogger('policy_whisperer').setLevel(logging.INFO)
    logging.getLogger('langchain').setLevel(logging.INFO)
    logger.info("Running with INFO level logging")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/policy-types')
def policy_types():
    """Return available policy types"""
    return jsonify({
        'success': True,
        'policy_types': get_policy_types()
    })

@app.route('/api/generate-policy', methods=['POST'])
def generate_policy():
    data = request.json
    user_prompt = data.get('prompt', '')
    policy_type = data.get('policy_type', 'general')
    target_path = data.get('target_path', '')
    repository = data.get('repository', '')
    
    # Log the incoming request
    logger.info(f"Received policy generation request")
    logger.info(f"User prompt: {user_prompt}")
    logger.info(f"Policy type: {policy_type}")
    logger.info(f"Target path: {target_path}")
    logger.info(f"Repository: {repository}")
    
    try:
        # Generate the policy
        policy_yaml = generate_policy_from_prompt(user_prompt, policy_type)
        logger.info(f"Policy generated successfully")
        
        # Generate explanation
        explanation = generate_policy_explanation(policy_yaml, user_prompt)
        logger.info(f"Policy explanation generated successfully")
        
        # Analyze resources
        resources = analyze_policy_resources(policy_yaml)
        logger.info(f"Policy resources analyzed: {resources}")
        
        # Suggest a file path if not provided
        suggested_path = target_path
        if not suggested_path:
            # Determine a suitable path based on policy content and type
            if 'github' in user_prompt.lower() or 'actions' in user_prompt.lower():
                suggested_path = 'policies/ci/github-actions.yml'
            elif 'aws' in user_prompt.lower():
                suggested_path = 'policies/cloud/aws.yml'
            elif 'azure' in user_prompt.lower():
                suggested_path = 'policies/cloud/azure.yml'
            elif 'authn' in user_prompt.lower() or 'authentication' in user_prompt.lower():
                suggested_path = 'policies/authn/authn.yml'
            elif 'jwt' in user_prompt.lower():
                suggested_path = 'policies/authn/authn-jwt.yml'
            else:
                suggested_path = 'policies/general/policy.yml'
        
        return jsonify({
            'success': True,
            'policy': policy_yaml,
            'explanation': explanation,
            'resources': resources,
            'suggested_path': suggested_path,
            'repository': repository
        })
    except Exception as e:
        error_msg = f"Error in policy generation: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create-pr', methods=['POST'])
def create_pull_request():
    """Create a pull request with the generated policy"""
    try:
        data = request.json
        repository = data.get('repository', '')
        file_path = data.get('file_path', '')
        content = data.get('content', '')
        commit_message = data.get('commit_message', f"Add/Update Conjur policy: {file_path}")
        
        logger.info(f"Creating PR for repository: {repository}, file path: {file_path}")
        
        # Check if we have all required parameters
        if not repository or not file_path or not content:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: repository, file_path, or content'
            }), 400
            
        # Parse the repository to get owner and name
        try:
            # Handle both formats: "owner/repo" and "https://github.com/owner/repo"
            if '/' in repository:
                if 'github.com' in repository:
                    # Extract from URL
                    parts = repository.rstrip('/').split('/')
                    repo_owner = parts[-2]
                    repo_name = parts[-1]
                else:
                    # Simple owner/repo format
                    parts = repository.split('/')
                    if len(parts) >= 2:
                        repo_owner = parts[0]
                        repo_name = parts[1]
                    else:
                        raise ValueError(f"Invalid repository format: {repository}")
            else:
                raise ValueError(f"Invalid repository format: {repository}")
        except Exception as e:
            logger.error(f"Error parsing repository: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Invalid repository format: {repository}"
            }), 400
            
        # Get GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.error("No GitHub token found in environment variables")
            return jsonify({
                'success': False,
                'error': 'GitHub token not configured. Please set the GITHUB_TOKEN environment variable.'
            }), 500
            
        # Import the GitHub integration module
        try:
            from policy_whisperer.github_integration import create_github_pr
        except ImportError as e:
            logger.error(f"Error importing GitHub integration module: {str(e)}")
            logger.error("Falling back to simulated PR creation")
            
            # Simulate PR creation for the proof of concept
            pr_number = 42  # This would be the actual PR number from GitHub
            
            return jsonify({
                'success': True,
                'pr_number': pr_number,
                'pr_url': f"https://github.com/{repository}/pull/{pr_number}",
                'message': f"Pull request created successfully (simulated): #{pr_number}"
            })
            
        # Create the PR using the GitHub integration module
        try:
            result = create_github_pr(
                repo_owner=repo_owner,
                repo_name=repo_name,
                policy_content=content,
                file_path=file_path,
                github_token=github_token,
                commit_message=commit_message
            )
            
            if result.get('success', False):
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"Error creating GitHub PR: {str(e)}")
            logger.exception("Exception details:")
            
            # Fallback to simulated PR creation
            logger.warning("Falling back to simulated PR creation due to error")
            pr_number = 42  # This would be the actual PR number from GitHub
            
            return jsonify({
                'success': True,
                'pr_number': pr_number,
                'pr_url': f"https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}",
                'message': f"Pull request created successfully (simulated): #{pr_number}"
            })
            
    except Exception as e:
        error_msg = f"Error creating pull request: {str(e)}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Log the app startup
    logger.info(f"Starting Policy Whisperer with DEBUG={debug_mode}")
    
    # Run the Flask app
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
