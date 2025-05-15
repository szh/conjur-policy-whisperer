"""
Example selector for Policy Whisperer

This module uses LLM to identify the most relevant examples for a given policy request.
"""

import logging
import json
from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

from policy_whisperer.llm_client import get_llm
from policy_whisperer.templates import POLICY_STRUCTURE, fetch_policy_template

logger = logging.getLogger(__name__)

def identify_relevant_examples(user_prompt: str, max_examples: int = 3) -> List[Dict[str, str]]:
    """
    Use LLM to identify the most relevant example files for a given policy request.
    
    Args:
        user_prompt: The user's policy request
        max_examples: Maximum number of examples to return
        
    Returns:
        List of dictionaries containing category, file_name, and relevance_score
    """
    try:
        logger.info(f"Identifying relevant examples for prompt: {user_prompt}")
        
        # Create a flattened list of all available templates
        all_templates = []
        
        for category, value in POLICY_STRUCTURE.items():
            if isinstance(value, list):
                # Simple category with list of files
                for file_name in value:
                    all_templates.append({
                        "category": category,
                        "file_name": file_name.replace(".yml", ""),
                        "path": f"{category}/{file_name}"
                    })
            elif isinstance(value, dict):
                # Nested category
                for subcategory, files in value.items():
                    for file_name in files:
                        all_templates.append({
                            "category": f"{category}/{subcategory}",
                            "file_name": file_name.replace(".yml", ""),
                            "path": f"{category}/{subcategory}/{file_name}"
                        })
        
        # Create a prompt for the LLM to identify relevant examples
        example_selector_template = """
        You are an expert in Conjur policies. Your task is to identify the most relevant example files for a given policy request.
        
        User's policy request: "{user_prompt}"
        
        Available example files:
        {available_examples}
        
        Based on the user's request, identify the {max_examples} most relevant example files that would be helpful for generating this policy.
        For each example, provide a relevance score between 0 and 100, where 100 means perfectly relevant.
        
        Return your response as a JSON array with objects containing these fields:
        - category: The category of the example
        - file_name: The name of the file without extension
        - relevance_score: A number between 0-100 indicating relevance
        - reason: A brief explanation of why this example is relevant
        
        Example response format:
        [
            {{"category": "authn", "file_name": "authn-jwt-github", "relevance_score": 95, "reason": "This example is highly relevant because it demonstrates JWT authentication for GitHub."}},
            {{"category": "ci/github", "file_name": "actions", "relevance_score": 85, "reason": "This example shows GitHub Actions integration which matches the user's request."}}
        ]
        
        IMPORTANT: Return ONLY the JSON array, nothing else. Ensure the JSON is valid.
        """
        
        # Format the available examples for the prompt
        available_examples_text = "\n".join([
            f"- {template['category']}/{template['file_name']}" 
            for template in all_templates
        ])
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_template(example_selector_template)
        
        # Initialize the LLM - use a smaller model for cost efficiency
        model = get_llm(model_name="gpt-4o", temperature=0.3)
        
        # Create the chain
        chain = (
            prompt
            | model
            | StrOutputParser()
        )
        
        # Execute the chain
        response = chain.invoke({
            "user_prompt": user_prompt,
            "available_examples": available_examples_text,
            "max_examples": max_examples
        })
        
        logger.debug(f"LLM response for example selection: {response}")
        
        # Parse the JSON response
        try:
            examples = json.loads(response)
            
            # Validate and sort by relevance score
            valid_examples = []
            for example in examples:
                if all(key in example for key in ["category", "file_name", "relevance_score"]):
                    valid_examples.append(example)
            
            # Sort by relevance score (highest first)
            valid_examples.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # Limit to max_examples
            valid_examples = valid_examples[:max_examples]
            
            logger.info(f"Identified {len(valid_examples)} relevant examples: {valid_examples}")
            return valid_examples
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            return []
            
    except Exception as e:
        logger.error(f"Error identifying relevant examples: {e}")
        logger.exception("Exception details:")
        return []

def fetch_relevant_examples(user_prompt: str, max_examples: int = 3) -> Dict[str, str]:
    """
    Fetch the content of the most relevant example files for a given policy request.
    
    Args:
        user_prompt: The user's policy request
        max_examples: Maximum number of examples to fetch
        
    Returns:
        Dictionary mapping example paths to their content
    """
    # Identify relevant examples
    relevant_examples = identify_relevant_examples(user_prompt, max_examples)
    
    # Fetch the content of each example
    examples_content = {}
    
    for example in relevant_examples:
        category = example["category"]
        file_name = example["file_name"]
        
        # Fetch the template content
        template_content = fetch_policy_template(category, file_name)
        
        if template_content:
            # Add to the examples content dictionary
            example_path = f"{category}/{file_name}"
            examples_content[example_path] = {
                "content": template_content,
                "relevance_score": example.get("relevance_score", 0),
                "reason": example.get("reason", "")
            }
            logger.info(f"Fetched content for example: {example_path}")
        else:
            logger.warning(f"Failed to fetch content for example: {category}/{file_name}")
    
    return examples_content
