"""
Project Context Manager for Samoey Copilot
Intelligent project context management that understands relationships between projects
and maintains contextual awareness for personalized AI assistance
"""

import os
import json
import ast
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import settings
from app.services.personal_learning import PersonalLearningEngine
from app.services.coding_style_analyzer import CodingStyleAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ProjectInfo:
    """Comprehensive information about a project"""
    project_path: str
    project_name: str
    project_type: str
    technologies: List[str]
    dependencies: List[str]
    complexity: str
    last_analyzed: str
    file_count: int
    total_lines: int
    main_languages: List[str]
    architecture_patterns: List[str]
    key_files: List[str]
    relationships: Dict[str, List[str]]
    metadata: Dict[str, Any]

@dataclass
class ProjectRelationship:
    """Relationship between projects"""
    source_project: str
    target_project: str
    relationship_type: str  # "dependency", "shared_code", "similar_structure", "technological"
    strength: float  # 0.0 to 1.0
    shared_elements: List[str]
    discovered_date: str

class ProjectContextManager:
    """
    Advanced project context manager that learns from user's projects
    and maintains intelligent contextual awareness
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.learning_engine = PersonalLearningEngine(user_id)
        self.style_analyzer = CodingStyleAnalyzer(user_id)
        self.user_data_dir = Path(settings.USER_DATA_DIR) / str(user_id)
        self.projects_path = self.user_data_dir / "projects.json"
        self.relationships_path = self.user_data_dir / "project_relationships.json"

        # Load existing data
        self.projects = self._load_projects()
        self.relationships = self._load_relationships()

    def _load_projects(self) -> Dict[str, ProjectInfo]:
        """Load existing project data"""
        if self.projects_path.exists():
            try:
                with open(self.projects_path, 'r') as f:
                    data = json.load(f)
                    return {path: ProjectInfo(**info) for path, info in data.items()}
            except Exception as e:
                logger.error(f"Error loading projects: {e}")

        return {}

    def _load_relationships(self) -> List[ProjectRelationship]:
        """Load existing project relationships"""
        if self.relationships_path.exists():
            try:
                with open(self.relationships_path, 'r') as f:
                    data = json.load(f)
                    return [ProjectRelationship(**rel) for rel in data]
            except Exception as e:
                logger.error(f"Error loading relationships: {e}")

        return []

    def analyze_project(self, project_path: str) -> ProjectInfo:
        """
        Analyze a project and extract comprehensive context information
        """
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        logger.info(f"Analyzing project: {project_path}")

        # Basic project information
        project_name = project_path.name
        project_type = self._detect_project_type(project_path)

        # Analyze files and structure
        file_analysis = self._analyze_project_structure(project_path)

        # Extract technologies and dependencies
        technologies = self._extract_technologies(project_path)
        dependencies = self._extract_dependencies(project_path)

        # Analyze architecture patterns
        architecture_patterns = self._analyze_architecture_patterns(project_path)

        # Identify key files
        key_files = self._identify_key_files(project_path)

        # Create project info
        project_info = ProjectInfo(
            project_path=str(project_path),
            project_name=project_name,
            project_type=project_type,
            technologies=technologies,
            dependencies=dependencies,
            complexity=file_analysis.get("complexity", "medium"),
            last_analyzed=datetime.now().isoformat(),
            file_count=file_analysis.get("file_count", 0),
            total_lines=file_analysis.get("total_lines", 0),
            main_languages=file_analysis.get("main_languages", []),
            architecture_patterns=architecture_patterns,
            key_files=key_files,
            relationships={},
            metadata={
                "analysis_duration": file_analysis.get("analysis_duration", 0),
                "scan_timestamp": datetime.now().isoformat(),
                "analysis_version": "1.0"
            }
        )

        # Store project info
        self.projects[str(project_path)] = project_info
        self._save_projects()

        # Update project relationships
        self._update_project_relationships(project_path)

        # Update learning engine
        self.learning_engine.add_project_context(str(project_path), asdict(project_info))

        logger.info(f"Project analysis completed: {project_name}")
        return project_info

    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project based on structure and files"""
        # Check for specific project indicators
        indicators = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock"],
            "node": ["package.json", "package-lock.json", "yarn.lock", "node_modules"],
            "django": ["manage.py", "settings.py", "wsgi.py"],
            "flask": ["app.py", "application.py"],
            "fastapi": ["main.py", "app.py"],
            "react": ["package.json", "src/", "public/"],
            "vue": ["package.json", "src/", "public/"],
            "angular": ["angular.json", "package.json", "src/"],
            "java": ["pom.xml", "build.gradle", "src/main/java/"],
            "go": ["go.mod", "go.sum", "main.go"],
            "rust": ["Cargo.toml", "src/main.rs"],
            "ruby": ["Gemfile", "Rakefile"],
            "php": ["composer.json", "index.php"],
            "cpp": ["CMakeLists.txt", "Makefile", "main.cpp"],
            "csharp": ["*.csproj", "Program.cs"]
        }

        project_files = [f.name for f in project_path.iterdir() if f.is_file()]
        project_dirs = [d.name for d in project_path.iterdir() if d.is_dir()]

        # Check for matches
        for project_type, files in indicators.items():
            for indicator in files:
                if indicator in project_files or indicator in project_dirs:
                    return project_type

        # Fallback to language detection
        return self._detect_primary_language(project_path)

    def _detect_primary_language(self, project_path: Path) -> str:
        """Detect primary programming language based on file extensions"""
        language_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx", ".ts", ".tsx"],
            "java": [".java"],
            "go": [".go"],
            "rust": [".rs"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cxx", ".cc", ".hpp", ".hxx"],
            "csharp": [".cs"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "kotlin": [".kt"],
            "scala": [".scala"],
            "r": [".r", ".R"],
            "typescript": [".ts", ".tsx"]
        }

        extension_counts = Counter()

        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                extension_counts[ext] += 1

        # Find the most common language
        for language, extensions in language_extensions.items():
            total_count = sum(extension_counts[ext] for ext in extensions)
            if total_count > 0:
                return language

        return "unknown"

    def _analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze the overall structure of the project"""
        start_time = datetime.now()

        # Count files and lines
        file_count = 0
        total_lines = 0
        language_counts = Counter()

        # Supported source code extensions
        source_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
                           ".cpp", ".c", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".r"}

        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                file_count += 1

                # Count lines for source files
                if file_path.suffix.lower() in source_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines

                        # Count by language
                        lang = self._get_language_from_extension(file_path.suffix)
                        if lang:
                            language_counts[lang] += 1
                    except Exception as e:
                        logger.debug(f"Could not read file {file_path}: {e}")

        # Determine main languages
