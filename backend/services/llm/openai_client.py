import os
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, OpenAIError
from ...core.config import settings

logger = logging.getLogger(__name__)

# Global client instance
_client = None

def get_openai_client():
    """Get a singleton instance of the OpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-4",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """Make a chat completion request to the OpenAI API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: The model to use (default: gpt-4)
        temperature: Controls randomness (0-2)
        max_tokens: Maximum number of tokens to generate
        **kwargs: Additional parameters for the API call
        
    Returns:
        Dictionary containing the API response
    """
    client = get_openai_client()
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_completion: {str(e)}")
        raise

async def generate_embedding(
    text: str, 
    model: str = "text-embedding-ada-002"
) -> List[float]:
    """Generate an embedding for the given text.
    
    Args:
        text: The text to generate an embedding for
        model: The embedding model to use
        
    Returns:
        List of floats representing the embedding
    """
    client = get_openai_client()
    
    try:
        response = await client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except OpenAIError as e:
        logger.error(f"OpenAI embedding error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_embedding: {str(e)}")
        raise

async def moderate_text(text: str) -> Dict[str, Any]:
    """Moderate the given text for content policy violations.
    
    Args:
        text: The text to moderate
        
    Returns:
        Dictionary containing moderation results
    """
    client = get_openai_client()
    
    try:
        response = await client.moderations.create(
            input=text
        )
        return response.results[0]
    except OpenAIError as e:
        logger.error(f"OpenAI moderation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in moderate_text: {str(e)}")
        raise
