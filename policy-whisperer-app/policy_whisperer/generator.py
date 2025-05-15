"""
Policy generation core functionality for Policy Whisperer
"""

import logging
import yaml
from typing import Dict, List, Optional, Any, Union

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

from policy_whisperer.llm_client import get_llm
from policy_whisperer.templates import (
    POLICY_STRUCTURE, 
    PREDEFINED_TEMPLATES, 
    fetch_policy_template
)
from policy_whisperer.utils import ConjurPolicyLoader
from policy_whisperer.example_selector import fetch_relevant_examples

logger = logging.getLogger(__name__)

def generate_policy_from_prompt(user_prompt: str, policy_type: str = "general") -> str:
    """
    Generate a Conjur policy based on user prompt and policy type using LangChain
    """
    try:
        logger.info(f"User prompt: {user_prompt}")
        logger.info(f"Initial policy type: {policy_type}")
        
        # Refine policy type based on user prompt and policy_structure.json
        user_prompt_lower = user_prompt.lower()
        
        # Load the policy structure to determine valid paths
        policy_structure = POLICY_STRUCTURE
        
        # Map of keywords to policy structure paths
        keyword_to_policy_map = {
            # Authentication methods
            "oidc": ("authn", "authn-oidc-webapp.yml"),
            "openid": ("authn", "authn-oidc-webapp.yml"),
            "azure ad": ("authn", "authn-azure.yml"),
            "azure authentication": ("authn", "authn-azure.yml"),
            "gcp authentication": ("authn", "authn-gcp.yml"),
            "iam": ("authn", "authn-iam-prod.yml"),
            "k8s authentication": ("authn", "authn-k8s.yml"),
            
            # JWT authentication
            "github jwt": ("authn", "authn-jwt-github.yml"),
            "github authentication": ("authn", "authn-jwt-github.yml"),
            "gitlab jwt": ("authn", "authn-jwt-gitlab.yml"),
            "jenkins jwt": ("authn", "authn-jwt-jenkins.yml"),
            
            # CI systems
            "github actions": ("ci/github", "actions.yml"),
            "github": ("ci/github", "github.yml"),
            "gitlab": ("ci/gitlab", "gitlab.yml"),
            "jenkins": ("ci/jenkins", "jenkins.yml"),
            
            # Cloud providers
            "aws": ("cloud/aws", "aws.yml"),
            "ec2": ("cloud/aws", "ec2.yml"),
            "ecs": ("cloud/aws", "ecs.yml"),
            "lambda": ("cloud/aws", "lambda.yml"),
            "azure": ("cloud/azure", "azure.yml"),
            "azure devops": ("cloud/azure", "devops.yml"),
            "azure function": ("cloud/azure", "function.yml"),
            "gcp": ("cloud/gcp", "gcp.yml"),
            "google compute": ("cloud/gcp", "compute.yml"),
            "google function": ("cloud/gcp", "function.yml"),
            
            # CD systems
            "ansible": ("cd/ansible", "ansible.yml"),
            "kubernetes": ("cd/kubernetes", "kubernetes.yml"),
            "k8s": ("cd/kubernetes", "kubernetes.yml"),
            "terraform": ("cd/terraform", "terraform.yml"),
            
            # Web applications
            "web application": ("web", "conjur-oidc-demo.yml"),
            "web app": ("web", "conjur-oidc-demo.yml"),
        }
        
        # Find the most specific match in the user prompt
        best_match = None
        best_match_length = 0
        
        for keyword, path_info in keyword_to_policy_map.items():
            if keyword in user_prompt_lower and len(keyword) > best_match_length:
                best_match = path_info
                best_match_length = len(keyword)
                logger.info(f"Found keyword match: {keyword} -> {path_info}")
        
        if best_match:
            category, template = best_match
            policy_type = category
            template_name = template.replace(".yml", "")
            logger.info(f"Detected policy type: {policy_type}, template: {template_name}")
        else:
            # If no specific match, keep the general type or use a default
            if policy_type == "general":
                logger.info("No specific policy type detected, using general")
                
                # Check for general categories
                if "authentication" in user_prompt_lower or "auth" in user_prompt_lower:
                    policy_type = "authn"
                    logger.info("Detected general authentication request")
                elif "ci" in user_prompt_lower or "continuous integration" in user_prompt_lower:
                    policy_type = "ci"
                    logger.info("Detected general CI request")
                elif "cd" in user_prompt_lower or "continuous delivery" in user_prompt_lower or "deployment" in user_prompt_lower:
                    policy_type = "cd"
                    logger.info("Detected general CD request")
                elif "cloud" in user_prompt_lower:
                    policy_type = "cloud"
                    logger.info("Detected general cloud request")
        
        logger.info(f"Refined policy type: {policy_type}")
        
        try:
            # Prepare system prompt with Conjur policy knowledge
            system_template = """
            You are a Conjur Policy Generator assistant. Your task is to generate valid Conjur policy YAML based on the user's requirements.
            

You are a Conjur policy expert. Generate valid YAML Conjur policy with the following constraints:

1. Only use these resource tags: !policy, !user, !group, !host, !variable, !webservice, !grant, !permit, !delete.
2. Each resource starts with `-`. Use flat layout unless nesting is essential.
3. Fields:
- All resources (except grant/permit/delete) require `id`; optional `annotations` must be meaningful.
- !policy may contain `body:` with inline resources but avoid deep nesting.
- !grant: use `role`, and `member` or `members`.
- !permit: use `role`, `privileges`, and `resource` or `resources`.
- !delete: use `record: !<type> <id>`.
4. Use YAML anchors (&name) and aliases (*name) to reuse host or variable lists.
5. Do not reference undeclared entities.
6. Do not store secret values—only declare !variable.
7. Prefer short, hyphenated lowercase IDs.
8. Authenticator policies must follow this format:
- Path: conjur/authn-<type>/<service-id> (e.g. conjur/authn-jwt/github)
- Define matching !webservice in body
- Add required variables (issuer, jwks-uri, token-app-property, etc.)
- Add !group consumers and !permit for authenticate privilege
- Matching host annotations are required for some authenticators, rely on the examples for this.

Avoid: placeholders, fictional references, deep nesting, boilerplate annotations like editable: true unless required.

Goal: Output should be syntactically correct, minimal, and ready for `conjur policy load`.

            Conjur policies follow these rules:
            1. They are written in YAML format with .yml extension
            2. Nodes start with a dash and a space followed by a tag (e.g., - !user)
            3. Common tags include: !policy, !user, !host, !group, !variable, !grant, !permit, !webservice
            4. Policies can be nested inside other policies
            5. Annotations can be added to provide metadata
            6. Variables can be defined to store sensitive data
            7. Permissions are granted using !grant and !permit tags
            8. COMMENT HEAVILY THE POLICY RESOURCES!!!
            9. IGNORE COMPLIANCE AND AUDIT ANNOTATIONS in the examples!
            10. DO NOT ADD A "conjur policy load root authn/authn-oidc/customer-portal.yml" comment IN THE POLICY
            11. NOTE: that an authenticator isn't always needed. It depends on the use case. 
            
            The user has requested a policy for: {user_prompt}
            
            {examples}
            
            Generate a complete, valid Conjur policy tailored to the user's request. Follow Conjur best practices, including clear structure, annotations, and descriptions. Reflect any mentioned resources, credentials, permissions, environments, or applications. Do not ask for clarification. Output only the YAML—no explanations or formatting.            """
            
            # Use the example selector to find the most relevant examples for this request
            logger.info("Using intelligent example selection to find relevant templates")
            relevant_examples = fetch_relevant_examples(user_prompt, max_examples=3)
            
            # Prepare examples based on the selected relevant examples
            examples_text = ""
            
            if relevant_examples:
                logger.info(f"Found {len(relevant_examples)} relevant examples")
                
                # Add each relevant example with its explanation
                for example_path, example_data in relevant_examples.items():
                    content = example_data["content"]
                    reason = example_data.get("reason", "")
                    score = example_data.get("relevance_score", 0)
                    
                    # Add the example with its relevance information
                    examples_text += f"\nExample {example_path} policy (relevance: {score}%):\n"
                    if reason:
                        examples_text += f"Reason for selection: {reason}\n"
                    examples_text += f"```yaml\n{content}\n```\n"
                    
                    logger.info(f"Added relevant example: {example_path} (score: {score})")
            else:
                # Fallback to using predefined templates if no relevant examples were found
                logger.warning("No relevant examples found, falling back to predefined templates")
                
                # Try to get a template based on the detected policy type
                if policy_type in PREDEFINED_TEMPLATES:
                    template = PREDEFINED_TEMPLATES[policy_type]
                    examples_text += f"\nExample {policy_type} policy:\n```yaml\n{template}\n```\n"
                    logger.info(f"Using predefined template for {policy_type}")
                elif '/' in policy_type:
                    # Try to find a matching predefined template
                    for key, template in PREDEFINED_TEMPLATES.items():
                        if key == policy_type or key.startswith(f"{policy_type}/"):
                            examples_text += f"\nExample {key} policy:\n```yaml\n{template}\n```\n"
                            logger.info(f"Using predefined template {key} for {policy_type}")
                            break
                
                # If still no examples, add some general examples
                if not examples_text:
                    logger.warning("No examples found, using general examples")
                    
                    # Add examples for common policy types
                    examples_added = 0
                    for category, template in PREDEFINED_TEMPLATES.items():
                        if examples_added < 2:  # Limit to 2 examples
                            examples_text += f"\nExample {category} policy:\n```yaml\n{template}\n```\n"
                            logger.info(f"Adding general example for {category}")
                            examples_added += 1
            
            # Create the prompt template
            prompt = ChatPromptTemplate.from_template(system_template)
            
            # Initialize the LLM
            model = get_llm(model_name="gpt-4o", temperature=0.7)
                
            # Create the chain
            chain = (
                prompt
                | model
                | StrOutputParser()
            )
            
            # Log the prompt for debugging
            logger.debug(f"Prompt: {system_template.format(user_prompt=user_prompt, examples=examples_text)}")
            
            # Execute the chain
            generated_policy = chain.invoke({"user_prompt": user_prompt, "examples": examples_text})
            
            # Clean up the generated policy
            generated_policy = generated_policy.strip()
            
            # If the policy is wrapped in ```yaml and ```, remove them
            if generated_policy.startswith("```yaml"):
                generated_policy = generated_policy[7:]
            if generated_policy.startswith("```"):
                generated_policy = generated_policy[3:]
            if generated_policy.endswith("```"):
                generated_policy = generated_policy[:-3]
            
            generated_policy = generated_policy.strip()
            
            # Validate the generated policy as valid YAML with Conjur tags
            try:
                yaml.load(generated_policy, Loader=ConjurPolicyLoader)
                logger.info("Generated policy is valid YAML")
            except Exception as yaml_error:
                logger.warning(f"Generated policy is not valid YAML: {yaml_error}")
                # We'll still return the policy, but log the warning
            
            return generated_policy
        
        except Exception as e:
            error_msg = f"Error generating policy: {e}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            raise Exception(f"Failed to generate policy: {str(e)}")
        
    except Exception as e:
        error_msg = f"Error generating policy: {e}"
        logger.error(error_msg)
        logger.exception("Exception details:")
        raise Exception(f"Failed to generate policy: {str(e)}")

def generate_policy_explanation(policy: str, user_prompt: str) -> str:
    """
    Generate a concise markdown explanation of the policy based on the policy content and user prompt
    """
    try:
        # Prepare a prompt for generating the explanation request
        logger.info(f"Sending policy explanation request using LangChain")
        logger.info(f"User prompt that led to this policy: {user_prompt}")
        
        # Prepare a prompt for generating the explanation
        explanation_template = """
        Generate a CONCISE explanation of the following Conjur policy in markdown format.
        
        ```yaml
        {policy}
        ```
        
        The user requested: "{user_prompt}"
        
        Your explanation MUST:
        1. Be formatted in clean, simple markdown
        2. Start with a brief one-sentence summary of what the policy does
        3. Use bullet points for listing resources and permissions
        4. Be EXTREMELY CONCISE - no more than 200 words total
        5. Focus only on the most important aspects of the policy
        
        Include these sections (using markdown headers):
        - **Summary**: One sentence overview
        - **Key Resources**: Bullet list of main resources (max 5)
        - **Access Rules**: Bullet list of main permissions (max 3)
        - **Usage Notes**: 1-2 brief tips for implementation (if relevant)
        
        DO NOT include lengthy explanations, code examples, or theoretical discussions.
        """
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_template(explanation_template)
        
        # Initialize the LLM (using a smaller model for explanations to save costs)
        # For Azure OpenAI, this will use the deployment name from AZURE_OPENAI_GPT35_DEPLOYMENT
        logger.info("Using GPT-4o model for policy explanation")
        
        # In Azure OpenAI, we need to use the exact deployment name that's configured in the portal
        # This will be handled by the get_llm function
        model = get_llm(model_name="gpt-4o", temperature=0.5)
        
        # Create the chain
        chain = (
            prompt
            | model
            | StrOutputParser()
        )
        
        # Log the explanation prompt for debugging
        logger.debug(f"Explanation prompt: {explanation_template.format(policy=policy, user_prompt=user_prompt)}")
        
        # Execute the chain
        explanation = chain.invoke({"policy": policy, "user_prompt": user_prompt})
        
        # Ensure consistent markdown formatting
        # If the explanation is wrapped in markdown code blocks, extract the content
        if explanation.strip().startswith('```markdown') or explanation.strip().startswith('```md'):
            # Extract content between markdown code blocks
            import re
            match = re.search(r'```(?:markdown|md)\s*([\s\S]*?)```', explanation)
            if match:
                explanation = match.group(1).strip()
        elif explanation.strip().startswith('```') and explanation.strip().endswith('```'):
            # Extract content between generic code blocks
            explanation = explanation.replace(explanation.split('\n')[0], '').replace('```', '').strip()
        
        # Ensure the explanation has proper markdown headers if they're missing
        if not any(line.strip().startswith('#') for line in explanation.split('\n')):
            # Add minimal markdown structure if none exists
            sections = explanation.split('\n\n')
            if len(sections) >= 1:
                # Add header to first section if it doesn't have one
                if not sections[0].strip().startswith('#'):
                    sections[0] = f"## Summary\n\n{sections[0]}"
                
                # Try to identify and add headers to other sections
                for i in range(1, len(sections)):
                    section = sections[i].strip()
                    if section and not section.startswith('#'):
                        # Check for common section indicators
                        if any(term in section.lower() for term in ['resource', 'contain']):
                            sections[i] = f"## Key Resources\n\n{section}"
                        elif any(term in section.lower() for term in ['access', 'permission', 'grant']):
                            sections[i] = f"## Access Rules\n\n{section}"
                        elif any(term in section.lower() for term in ['note', 'implementation', 'usage']):
                            sections[i] = f"## Usage Notes\n\n{section}"
                
                explanation = '\n\n'.join(sections)
        
        logger.info("Generated markdown explanation with proper formatting")
        return explanation
    
    except Exception as e:
        error_msg = f"Error generating explanation: {e}"
        logger.error(error_msg)
        logger.exception("Exception details for explanation generation:")
        return "Unable to generate a detailed explanation for this policy. Please review the policy content directly."
