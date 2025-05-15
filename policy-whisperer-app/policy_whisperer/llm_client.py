"""
LLM client setup for Policy Whisperer
"""

import os
import logging
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import AzureChatOpenAI

# Load environment variables for API keys if needed
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Get OpenAI API type from environment
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "openai").lower()

def get_llm(model_name="gpt-4", temperature=0.7):
    """
    Initialize the appropriate language model based on environment configuration
    """
    if OPENAI_API_TYPE == "azure":
        # Get Azure OpenAI configuration from environment
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        
        # Get the appropriate deployment name based on the model
        # In Azure OpenAI, we use the deployment name directly rather than model name
        # The deployment name should match what's configured in the Azure portal
        if "gpt-4" in model_name:
            deployment_name = os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT")
            logger.info(f"Using GPT-4 deployment: {deployment_name}")
        else:  # For GPT-3.5 models
            deployment_name = os.getenv("AZURE_OPENAI_GPT35_DEPLOYMENT")
            logger.info(f"Using GPT-3.5 deployment: {deployment_name}")
        
        if not all([api_key, endpoint, deployment_name]):
            logger.warning("Azure OpenAI configuration incomplete. Falling back to regular OpenAI.")
            return ChatOpenAI(model_name=model_name, temperature=temperature)
        
        logger.info(f"Using Azure OpenAI with deployment: {deployment_name}")
        try:
            # For Azure OpenAI, we don't need to specify model_name, just the deployment name
            # The model is already associated with the deployment in Azure OpenAI Studio
            logger.info(f"Initializing AzureChatOpenAI with deployment: {deployment_name}")
            return AzureChatOpenAI(
                openai_api_key=api_key,
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_version=api_version,
                temperature=temperature,
                # Don't pass model_name for Azure OpenAI
                # model_name=model_name
            )
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI: {e}")
            logger.exception("Exception details:")
            logger.warning("Falling back to regular OpenAI due to Azure initialization error")
            return ChatOpenAI(model_name=model_name, temperature=temperature)
    
    # Default to regular OpenAI
    logger.info(f"Using regular OpenAI with model: {model_name}")
    return ChatOpenAI(model_name=model_name, temperature=temperature)
