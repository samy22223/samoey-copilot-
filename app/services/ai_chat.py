import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.core.config import settings
from ai_team.mlops import MLOpsManager
from ai_team.orchestrator import AIOrchestrator
from ai_team.team import AITeam, TeamRole


class AIChatService:
    """
    Service for handling AI chat functionality.
    Integrates with multiple AI models and provides conversation management.
    """

    def __init__(self):
        self.mlops_manager = MLOpsManager()
        self.ai_orchestrator = AIOrchestrator()
        self.ai_team = AITeam()
        self.conversations: Dict[str, List[Dict]] = {}

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process a user message and generate AI response.
        """
        try:
            # Generate or use conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # Initialize conversation if it doesn't exist
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            # Add user message to conversation
            user_message = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "language": language
            }
            self.conversations[conversation_id].append(user_message)

            # Determine the best AI model and approach
            response = await self._generate_ai_response(message, conversation_id, language)

            # Add AI response to conversation
            ai_message = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": response["response"],
                "timestamp": datetime.now().isoformat(),
                "model_used": response.get("model", "unknown"),
                "confidence": response.get("confidence", 0.0)
            }
            self.conversations[conversation_id].append(ai_message)

            return {
                "response": response["response"],
                "conversation_id": conversation_id,
                "message_id": ai_message["id"],
                "timestamp": ai_message["timestamp"],
                "model_used": response.get("model", "unknown"),
                "confidence": response.get("confidence", 0.0)
            }

        except Exception as e:
            # Fallback response
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "model_used": "fallback",
                "confidence": 0.0
            }

    async def _generate_ai_response(
        self,
        message: str,
        conversation_id: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Generate AI response using the best available model.
        """
        try:
            # Get conversation context
            context = self._get_conversation_context(conversation_id)

            # Determine if this is a coding task
            is_coding_task = self._is_coding_task(message)

            if is_coding_task:
                # Use code generation model
                response = await self.mlops_manager.generate_code(
                    prompt=f"{context}\n\nUser: {message}",
                    language=self._detect_programming_language(message)
                )
                model_used = "phind-codellama"
            else:
                # Use text generation model
                system_prompt = f"You are Samoey Copilot, an advanced AI assistant. Respond in {language}."
                full_prompt = f"{system_prompt}\n\n{context}\n\nUser: {message}\n\nAssistant:"

                response = await self.mlops_manager.generate_text(
                    prompt=full_prompt,
                    model_name="mistral"
                )
                model_used = "mistral"

            # Extract response text
            if isinstance(response, dict) and "generated_text" in response:
                response_text = response["generated_text"]
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Clean up response
            response_text = self._clean_response(response_text)

            return {
                "response": response_text,
                "model": model_used,
                "confidence": 0.85
            }

        except Exception as e:
            # Try fallback model
            try:
                response = await self.mlops_manager.generate_text(
                    prompt=message,
                    model_name="llama3"
                )
                return {
                    "response": str(response),
                    "model": "llama3",
                    "confidence": 0.7
                }
            except:
                return {
                    "response": "I'm sorry, but I'm having trouble processing your request right now. Please try again later.",
                    "model": "fallback",
                    "confidence": 0.1
                }

    def _get_conversation_context(self, conversation_id: str, max_messages: int = 10) -> str:
        """
        Get conversation context for AI processing.
        """
        if conversation_id not in self.conversations:
            return ""

        messages = self.conversations[conversation_id][-max_messages:]
        context_parts = []

        for msg in messages:
            if msg["role"] == "user":
                context_parts.append(f"User: {msg['content']}")
            else:
                context_parts.append(f"Assistant: {msg['content']}")

        return "\n".join(context_parts)

    def _is_coding_task(self, message: str) -> bool:
        """
        Determine if the message is a coding-related task.
        """
        coding_keywords = [
            "code", "function", "class", "algorithm", "debug", "implement",
            "write", "create", "develop", "program", "script", "software",
            "python", "javascript", "java", "cpp", "html", "css", "sql",
            "bug", "error", "fix", "optimize", "refactor", "api", "database"
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in coding_keywords)

    def _detect_programming_language(self, message: str) -> str:
        """
        Detect the programming language from the message.
        """
        language_mapping = {
            "python": ["python", "py", "django", "flask", "pandas", "numpy"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "java": ["java", "spring", "android"],
            "cpp": ["c++", "cpp", "c plus plus"],
            "c": ["c language", "c programming"],
            "html": ["html", "html5", "web"],
            "css": ["css", "stylesheet", "styling"],
            "sql": ["sql", "database", "query"],
            "php": ["php", "laravel"],
            "ruby": ["ruby", "rails"],
            "go": ["go", "golang"],
            "rust": ["rust", "cargo"],
            "typescript": ["typescript", "ts"]
        }

        message_lower = message.lower()

        for lang, keywords in language_mapping.items():
            if any(keyword in message_lower for keyword in keywords):
                return lang

        return "python"  # Default to Python

    def _clean_response(self, response: str) -> str:
        """
        Clean up AI response text.
        """
        # Remove extra whitespace
        response = response.strip()

        # Remove common AI artifacts
        response = response.replace("Assistant:", "").replace("User:", "")

        # Remove excessive newlines
        while "\n\n\n" in response:
            response = response.replace("\n\n\n", "\n\n")

        return response.strip()

    async def get_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get list of conversations with metadata.
        """
        conversation_list = []

        for conv_id, messages in list(self.conversations.items())[offset:offset + limit]:
            if messages:
                conversation_list.append({
                    "id": conv_id,
                    "created_at": messages[0]["timestamp"],
                    "updated_at": messages[-1]["timestamp"],
                    "message_count": len(messages),
                    "last_message": messages[-1]["content"][:100] + "..." if len(messages[-1]["content"]) > 100 else messages[-1]["content"]
                })

        # Sort by updated_at
        conversation_list.sort(key=lambda x: x["updated_at"], reverse=True)

        return conversation_list

    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a specific conversation by ID.
        """
        if conversation_id not in self.conversations:
            return None

        return {
            "id": conversation_id,
            "messages": self.conversations[conversation_id],
            "created_at": self.conversations[conversation_id][0]["timestamp"] if self.conversations[conversation_id] else None,
            "updated_at": self.conversations[conversation_id][-1]["timestamp"] if self.conversations[conversation_id] else None
        }

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a specific conversation.
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    async def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation but keep the conversation.
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
            return True
        return False

    async def clear_all_conversations(self) -> None:
        """
        Clear all conversations.
        """
        self.conversations.clear()

    async def get_available_models(self) -> List[Dict]:
        """
        Get list of available AI models.
        """
        models = self.mlops_manager.get_available_models()

        model_info = []
        for model_name in models:
            model = self.mlops_manager.models.get(model_name)
            if model:
                model_info.append({
                    "name": model.name,
                    "type": model.model_type.value,
                    "provider": model.provider.value,
                    "languages": model.languages,
                    "size": model.model_size
                })

        return model_info

    async def get_team_status(self) -> Dict[str, Any]:
        """
        Get current status of the AI team.
        """
        return self.ai_team.get_team_status()

    async def create_project_plan(self, project_description: str) -> List[Dict[str, Any]]:
        """
        Create a project plan using the AI team.
        """
        return self.ai_orchestrator.create_project_plan()

    async def execute_task(self, task_description: str, task_type: str = "general") -> Dict[str, Any]:
        """
        Execute a specific task using the appropriate AI team member.
        """
        # Map task types to team roles
        role_mapping = {
            "architecture": TeamRole.ARCHITECT,
            "development": TeamRole.FULLSTACK_DEV,
            "frontend": TeamRole.FRONTEND_DEV,
            "backend": TeamRole.BACKEND_DEV,
            "ai": TeamRole.MLOPS,
            "testing": TeamRole.QA,
            "design": TeamRole.UI_DESIGNER,
            "documentation": TeamRole.DOCUMENTATION
        }

        role = role_mapping.get(task_type, TeamRole.FULLSTACK_DEV)

        # Create task for the AI team
        from ai_team.orchestrator import Task

        task = Task(
            name=task_description,
            description=task_description,
            assigned_role=role,
            status="pending"
        )

        # Execute the task
        result = await self.ai_orchestrator.execute_task(task)

        return {
            "task_id": task.name,
            "result": result,
            "status": "completed"
        }
