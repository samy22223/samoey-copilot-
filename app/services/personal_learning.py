"""
Personal Learning Engine for Samoey Copilot
Analyzes user's coding patterns, preferences, and development style
"""

import os
import json
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import logging

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class PersonalLearningEngine:
    """
    Core learning engine that analyzes and learns from user's development patterns
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_data_dir = Path(settings.USER_DATA_DIR) / str(user_id)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        # Learning data files
        self.style_profile_path = self.user_data_dir / "style_profile.json"
        self.project_context_path = self.user_data_dir / "project_context.json"
        self.knowledge_base_path = self.user_data_dir / "knowledge_base.json"

        # Initialize learning data
        self.style_profile = self._load_or_create_style_profile()
        self.project_context = self._load_or_create_project_context()
        self.knowledge_base = self._load_or_create_knowledge_base()

    def _load_or_create_style_profile(self) -> Dict[str, Any]:
        """Load or create user's coding style profile"""
        if self.style_profile_path.exists():
            try:
                with open(self.style_profile_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading style profile: {e}")

        # Default style profile
        return {
            "naming_conventions": {
                "variables": "camelCase",
                "functions": "camelCase",
                "classes": "PascalCase",
                "constants": "UPPER_CASE"
            },
            "indentation": {
                "style": "spaces",
                "size": 4
            },
            "code_patterns": {
                "preferred_frameworks": [],
                "common_libraries": [],
                "architecture_patterns": []
            },
            "error_handling": {
                "preferred_style": "try_catch",
                "logging_preference": True
            },
            "documentation": {
                "style": "docstrings",
                "coverage_preference": "high"
            },
            "performance": {
                "optimization_level": "balanced",
                "memory_concern": "medium"
            },
            "last_updated": datetime.now().isoformat()
        }

    def _load_or_create_project_context(self) -> Dict[str, Any]:
        """Load or create project context data"""
        if self.project_context_path.exists():
            try:
                with open(self.project_context_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading project context: {e}")

        return {
            "projects": {},
            "project_relationships": [],
            "common_dependencies": [],
            "development_patterns": {},
            "last_updated": datetime.now().isoformat()
        }

    def _load_or_create_knowledge_base(self) -> Dict[str, Any]:
        """Load or create personal knowledge base"""
        if self.knowledge_base_path.exists():
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")

        return {
            "code_snippets": [],
            "solutions": [],
            "patterns": [],
            "preferences": {},
            "learned_concepts": [],
            "last_updated": datetime.now().isoformat()
        }

    def analyze_code_style(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        Analyze coding style from a file and update style profile
        """
        try:
            # Parse the code
            tree = ast.parse(code_content)

            # Analyze naming conventions
            naming_analysis = self._analyze_naming_conventions(tree)

            # Analyze indentation patterns
            indentation_analysis = self._analyze_indentation(code_content)

            # Analyze code patterns
            patterns_analysis = self._analyze_code_patterns(code_content)

            # Analyze error handling
            error_analysis = self._analyze_error_handling(tree)

            # Analyze documentation
            doc_analysis = self._analyze_documentation(tree, code_content)

            # Update style profile with new insights
            self._update_style_profile({
                "naming_conventions": naming_analysis,
                "indentation": indentation_analysis,
                "code_patterns": patterns_analysis,
                "error_handling": error_analysis,
                "documentation": doc_analysis
            })

            return {
                "naming_conventions": naming_analysis,
                "indentation": indentation_analysis,
                "code_patterns": patterns_analysis,
                "error_handling": error_analysis,
                "documentation": doc_analysis
            }

        except Exception as e:
            logger.error(f"Error analyzing code style: {e}")
            return {}

    def _analyze_naming_conventions(self, tree: ast.AST) -> Dict[str, str]:
        """Analyze naming conventions used in the code"""
        variable_names = []
        function_names = []
        class_names = []
        constant_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variable_names.append(node.id)
            elif isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                class_names.append(node.name)

        # Analyze patterns
        variable_style = self._detect_naming_style(variable_names)
        function_style = self._detect_naming_style(function_names)
        class_style = self._detect_naming_style(class_names)

        return {
            "variables": variable_style,
            "functions": function_style,
            "classes": class_style,
            "constants": "UPPER_CASE"  # Default for constants
        }

    def _detect_naming_style(self, names: List[str]) -> str:
        """Detect the naming style from a list of names"""
        if not names:
            return "camelCase"

        camel_count = sum(1 for name in names if re.match(r'^[a-z][a-zA-Z0-9]*$', name))
        snake_count = sum(1 for name in names if re.match(r'^[a-z][a-z0-9_]*$', name))
        pascal_count = sum(1 for name in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

        if camel_count > snake_count and camel_count > pascal_count:
            return "camelCase"
        elif snake_count > camel_count and snake_count > pascal_count:
            return "snake_case"
        elif pascal_count > camel_count and pascal_count > snake_count:
            return "PascalCase"
        else:
            return "camelCase"  # Default

    def _analyze_indentation(self, code_content: str) -> Dict[str, Any]:
        """Analyze indentation patterns"""
        lines = code_content.split('\n')
        indent_sizes = []

        for line in lines:
            if line.strip():  # Non-empty line
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indent_sizes.append(leading_spaces)

        if not indent_sizes:
            return {"style": "spaces", "size": 4}

        # Find most common indent size
        indent_counter = Counter(indent_sizes)
        most_common_size = indent_counter.most_common(1)[0][0]

        return {
            "style": "spaces",  # Default to spaces
            "size": most_common_size
        }

    def _analyze_code_patterns(self, code_content: str) -> Dict[str, List[str]]:
        """Analyze code patterns and frameworks used"""
        patterns = {
            "preferred_frameworks": [],
            "common_libraries": [],
            "architecture_patterns": []
        }

        # Detect frameworks
        framework_indicators = {
            "react": ["React", "useState", "useEffect", "Component"],
            "django": ["django", "models.Model", "views.View"],
            "fastapi": ["FastAPI", "APIRouter", "Depends"],
            "flask": ["Flask", "app.route"],
            "express": ["express", "app.get", "app.post"],
            "next": ["NextPage", "getStaticProps"],
        }

        for framework, indicators in framework_indicators.items():
            if any(indicator in code_content for indicator in indicators):
                patterns["preferred_frameworks"].append(framework)

        # Detect common libraries
        library_imports = re.findall(r'import\s+(\w+)|from\s+(\w+)', code_content)
        for match in library_imports:
            lib = match[0] or match[1]
            if lib not in patterns["common_libraries"]:
                patterns["common_libraries"].append(lib)

        return patterns

    def _analyze_error_handling(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze error handling patterns"""
        try_except_blocks = []
        logging_statements = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                try_except_blocks.append("try_catch")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["print", "logging", "logger"]:
                        logging_statements.append(node.func.id)

        return {
            "preferred_style": "try_catch" if try_except_blocks else "none",
            "logging_preference": len(logging_statements) > 0
        }

    def _analyze_documentation(self, tree: ast.AST, code_content: str) -> Dict[str, Any]:
        """Analyze documentation patterns"""
        docstrings = []
        comments = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if ast.get_docstring(node):
                    docstrings.append(ast.get_docstring(node))

        # Count comments
        comment_lines = [line for line in code_content.split('\n') if line.strip().startswith('#')]

        return {
            "style": "docstrings" if docstrings else "comments",
            "coverage_preference": "high" if len(docstrings) > len(comment_lines) else "medium"
        }

    def _update_style_profile(self, new_insights: Dict[str, Any]):
        """Update the style profile with new insights"""
        for category, insights in new_insights.items():
            if category in self.style_profile:
                if isinstance(insights, dict):
                    for key, value in insights.items():
                        if isinstance(value, list):
                            # Merge lists, avoiding duplicates
                            existing = self.style_profile[category].get(key, [])
                            for item in value:
                                if item not in existing:
                                    existing.append(item)
                        else:
                            self.style_profile[category][key] = value
                else:
                    self.style_profile[category] = insights

        self.style_profile["last_updated"] = datetime.now().isoformat()
        self._save_style_profile()

    def _save_style_profile(self):
        """Save the style profile to disk"""
        try:
            with open(self.style_profile_path, 'w') as f:
                json.dump(self.style_profile, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving style profile: {e}")

    def add_project_context(self, project_path: str, project_info: Dict[str, Any]):
        """Add project context information"""
        project_name = Path(project_path).name

        self.project_context["projects"][project_name] = {
            "path": project_path,
            "type": project_info.get("type", "unknown"),
            "technologies": project_info.get("technologies", []),
            "dependencies": project_info.get("dependencies", []),
            "last_accessed": datetime.now().isoformat(),
            "complexity": project_info.get("complexity", "medium")
        }

        # Update common dependencies
        for dep in project_info.get("dependencies", []):
            if dep not in self.project_context["common_dependencies"]:
                self.project_context["common_dependencies"].append(dep)

        self.project_context["last_updated"] = datetime.now().isoformat()
        self._save_project_context()

    def _save_project_context(self):
        """Save project context to disk"""
        try:
            with open(self.project_context_path, 'w') as f:
                json.dump(self.project_context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving project context: {e}")

    def add_knowledge(self, knowledge_type: str, content: Dict[str, Any]):
        """Add knowledge to the personal knowledge base"""
        knowledge_entry = {
            "type": knowledge_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.8  # Default confidence
        }

        if knowledge_type == "code_snippet":
            self.knowledge_base["code_snippets"].append(knowledge_entry)
        elif knowledge_type == "solution":
            self.knowledge_base["solutions"].append(knowledge_entry)
        elif knowledge_type == "pattern":
            self.knowledge_base["patterns"].append(knowledge_entry)
        elif knowledge_type == "preference":
            self.knowledge_base["preferences"].update(content)
        elif knowledge_type == "learned_concept":
            self.knowledge_base["learned_concepts"].append(knowledge_entry)

        self.knowledge_base["last_updated"] = datetime.now().isoformat()
        self._save_knowledge_base()

    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

    def get_style_profile(self) -> Dict[str, Any]:
        """Get the current style profile"""
        return self.style_profile

    def get_project_context(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project context for a specific project"""
        return self.project_context["projects"].get(project_name)

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with their context"""
        return [
            {"name": name, **info}
            for name, info in self.project_context["projects"].items()
        ]

    def get_knowledge_base(self) -> Dict[str, Any]:
        """Get the personal knowledge base"""
        return self.knowledge_base

    def get_relevant_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant knowledge entries based on query"""
        relevant_entries = []

        # Search through all knowledge types
        for knowledge_type in ["code_snippets", "solutions", "patterns", "learned_concepts"]:
            if knowledge_type in self.knowledge_base:
                for entry in self.knowledge_base[knowledge_type]:
                    if self._is_relevant(query, entry):
                        relevant_entries.append(entry)

        # Sort by confidence and return top results
        relevant_entries.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return relevant_entries[:limit]

    def _is_relevant(self, query: str, entry: Dict[str, Any]) -> bool:
        """Check if a knowledge entry is relevant to the query"""
        query_lower = query.lower()
        content_str = str(entry.get("content", "")).lower()

        # Simple keyword matching (can be enhanced with more sophisticated NLP)
        return any(keyword in content_str for keyword in query_lower.split())

    def update_confidence(self, knowledge_type: str, content_hash: str, confidence: float):
        """Update confidence score for a knowledge entry"""
        if knowledge_type in self.knowledge_base:
            for entry in self.knowledge_base[knowledge_type]:
                if hash(str(entry["content"])) == hash(content_hash):
                    entry["confidence"] = confidence
                    self._save_knowledge_base()
                    break

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress"""
        return {
            "style_profile_last_updated": self.style_profile.get("last_updated"),
            "projects_tracked": len(self.project_context["projects"]),
            "knowledge_entries": {
                "code_snippets": len(self.knowledge_base.get("code_snippets", [])),
                "solutions": len(self.knowledge_base.get("solutions", [])),
                "patterns": len(self.knowledge_base.get("patterns", [])),
                "learned_concepts": len(self.knowledge_base.get("learned_concepts", []))
            },
            "common_dependencies": self.project_context.get("common_dependencies", []),
            "preferred_frameworks": self.style_profile.get("code_patterns", {}).get("preferred_frameworks", [])
        }

    def export_learning_data(self) -> Dict[str, Any]:
        """Export all learning data for backup or analysis"""
        return {
            "style_profile": self.style_profile,
            "project_context": self.project_context,
            "knowledge_base": self.knowledge_base,
            "export_timestamp": datetime.now().isoformat()
        }

    def import_learning_data(self, data: Dict[str, Any]):
        """Import learning data from backup"""
        if "style_profile" in data:
            self.style_profile = data["style_profile"]
            self._save_style_profile()

        if "project_context" in data:
            self.project_context = data["project_context"]
            self._save_project_context()

        if "knowledge_base" in data:
            self.knowledge_base = data["knowledge_base"]
            self._save_knowledge_base()

    def clear_learning_data(self):
        """Clear all learning data (for reset functionality)"""
        self.style_profile = self._load_or_create_style_profile()
        self.project_context = self._load_or_create_project_context()
        self.knowledge_base = self._load_or_create_knowledge_base()

        self._save_style_profile()
        self._save_project_context()
        self._save_knowledge_base()
