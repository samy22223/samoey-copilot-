"""
Code GPT Integration for Pinnacle Copilot

This module provides integration with Code GPT for AI-powered code assistance.
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

from ai_chat import get_chat_manager, AIChatManager

class CodeGPTRequest(BaseModel):
    """Request model for Code GPT API"""
    prompt: str
    code: Optional[str] = None
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    max_tokens: int = 2048
    temperature: float = 0.7

class CodeGPTResponse(BaseModel):
    """Response model for Code GPT API"""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    created: int

class CodeGPTIntegration:
    """Handles integration with Code GPT for AI-powered code assistance"""
    
    def __init__(self, chat_manager: AIChatManager):
        """Initialize with a chat manager instance"""
        self.chat_manager = chat_manager
        
    async def process_request(self, request: CodeGPTRequest) -> Dict[str, Any]:
        """
        Process a Code GPT request and return a formatted response.
        
        Args:
            request: The Code GPT request to process
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Build the full prompt with code context
            full_prompt = self._build_prompt(
                request.prompt, 
                request.code, 
                request.language, 
                request.context
            )
            
            # Process the message through the chat manager
            response = await self.chat_manager.process_message(
                full_prompt, 
                session_id="codegpt"
            )
            
            # Format the response for Code GPT
            return self._format_response(
                response, 
                prompt=request.prompt,
                code=request.code,
                model=request.model
            )
            
        except Exception as e:
            return self._format_error(str(e))
    
    def _build_prompt(
        self, 
        prompt: str, 
        code: Optional[str] = None, 
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a comprehensive prompt for the AI"""
        prompt_parts = [
            "Code GPT Request:",
            "",
            f"Language: {language}" if language else "",
            "",
            f"Code:\n```{language or ''}\n{code}\n```" if code else "",
            "",
            f"Context: {json.dumps(context, indent=2)}" if context else "",
            "",
            f"Prompt: {prompt}"
        ]
        return "\n".join(filter(None, prompt_parts))
    
    def _format_response(
        self, 
        response: Dict[str, Any],
        prompt: str,
        code: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format the response for Code GPT"""
        return {
            'success': True,
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': response.get('response', '')
                }
            }],
            'usage': {
                'prompt_tokens': len(prompt) + (len(code) if code else 0),
                'completion_tokens': len(response.get('response', '')),
                'total_tokens': (
                    len(prompt) + 
                    (len(code) if code else 0) + 
                    len(response.get('response', ''))
                )
            },
            'model': model or response.get('model', 'unknown'),
            'created': int(datetime.utcnow().timestamp())
        }
    
    def _format_error(self, error: str) -> Dict[str, Any]:
        """Format an error response"""
        return {
            'success': False,
            'error': error,
            'created': int(datetime.utcnow().timestamp())
        }

# Global instance
codegpt_integration = CodeGPTIntegration(get_chat_manager())
