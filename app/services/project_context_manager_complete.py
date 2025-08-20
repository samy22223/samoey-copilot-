"""
Complete Project Context Manager for Samoey Copilot
This file contains all the missing methods for the Project Context Manager
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

logger = logging.getLogger(__name__)

# Add the missing methods to complete the ProjectContextManager class

class ProjectContextManagerExtensions:
    """
    Extension methods for ProjectContextManager to complete functionality
    """

    def _parse_package_json_deps(self, config_path: Path) -> List[str]:
        """Parse package.json for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            # Extract both dependencies and devDependencies
            for section in ["dependencies", "devDependencies"]:
                if section in data:
                    dependencies.extend(data[section].keys())

        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        return dependencies

    def _parse_pyproject_deps(self, config_path: Path) -> List[str]:
        """Parse pyproject.toml for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Simple regex-based parsing for dependencies
            deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if deps_match:
                deps_content = deps_match.group(1)
                # Extract quoted strings
                dep_matches = re.findall(r'["\']([^"\']+)["\']', deps_content)
                dependencies.extend(dep_matches)

        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml: {e}")
        return dependencies

    def _parse_cargo_deps(self, config_path: Path) -> List[str]:
        """Parse Cargo.toml for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Extract dependencies section
            deps_section = re.search(r'\[dependencies\](.*?)(?=\[|$)', content, re.DOTALL)
            if deps_section:
                deps_content = deps_section.group(1)
                # Extract dependency names
                dep_matches = re.findall(r'^(\w+)\s*=', deps_content, re.MULTILINE)
                dependencies.extend(dep_matches)

        except Exception as e:
            logger.debug(f"Error parsing Cargo.toml: {e}")
        return dependencies

    def _parse_pom_deps(self, config_path: Path) -> List[str]:
        """Parse pom.xml for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Extract dependencies using regex
            dep_matches = re.findall(r'<dependency>.*?<artifactId>(.*?)</artifactId>.*?</dependency>', content, re.DOTALL)
            dependencies.extend(dep_matches)

        except Exception as e:
            logger.debug(f"Error parsing pom.xml: {e}")
        return dependencies

    def _parse_gradle_deps(self, config_path: Path) -> List[str]:
        """Parse build.gradle for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Extract implementation/compile dependencies
            impl_matches = re.findall(r'(?:implementation|compile|api)\s+["\']([^"\']+)["\']', content)
            dependencies.extend(impl_matches)

        except Exception as e:
            logger.debug(f"Error parsing build.gradle: {e}")
        return dependencies

    def _parse_gemfile_deps(self, config_path: Path) -> List[str]:
        """Parse Gemfile for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('gem '):
                        # Extract gem name
                        gem_match = re.search(r'gem\s+["\']([^"\']+)["\']', line)
                        if gem_match:
                            dependencies.append(gem_match.group(1))

        except Exception as e:
            logger.debug(f"Error parsing Gemfile: {e}")
        return dependencies

    def _parse_composer_deps(self, config_path: Path) -> List[str]:
        """Parse composer.json for dependencies"""
        dependencies = []
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            # Extract require section
            if "require" in data:
                dependencies.extend(data["require"].keys())

        except Exception as e:
            logger.debug(f"Error parsing composer.json: {e}")
        return dependencies

    def _analyze_architecture_patterns(self, project_path: Path) -> List[str]:
        """Analyze architectural patterns used in the project"""
        patterns = []

        # Check for common architectural patterns based on directory structure
        dir_structure = [d.name for d in project_path.iterdir() if d.is_dir()]

        # MVC Pattern
        if any(dir_name in dir_structure for dir_name in ["models", "views", "controllers"]):
            patterns.append("MVC")
        elif any(dir_name in dir_structure for dir_name in ["model", "view", "controller"]):
            patterns.append("MVC")

        # Layered Architecture
        if any(dir_name in dir_structure for dir_name in ["src", "lib", "config"]):
            patterns.append("Layered")

        # Microservices
        if "services" in dir_structure or "microservices" in dir_structure:
            patterns.append("Microservices")

        # Clean Architecture
        if any(dir_name in dir_structure for dir_name in ["entities", "use_cases", "interface_adapters"]):
            patterns.append("Clean Architecture")

        # Hexagonal Architecture
        if any(dir_name in dir_structure for dir_name in ["domain", "application", "infrastructure"]):
            patterns.append("Hexagonal Architecture")

        # Serverless
        if "functions" in dir_structure or "lambdas" in dir_structure:
            patterns.append("Serverless")

        # Monorepo
        if "packages" in dir_structure or "apps" in dir_structure:
            patterns.append("Monorepo")

        # Check for framework-specific patterns
        if project_path.name.lower().startswith("django"):
            patterns.append("Django MTV")
        elif "app" in dir_structure and "config" in dir_structure:
            patterns.append("Standard Web App")

        return patterns

    def _identify_key_files(self, project_path: Path) -> List[str]:
        """Identify key files in the project"""
        key_files = []

        # Configuration files
        config_patterns = [
            "package.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
            "pom.xml", "build.gradle", "Gemfile", "composer.json",
            "config.py", "settings.py", "application.properties", "app.config"
        ]

        # Main entry points
        entry_patterns = [
            "main.py", "app.py", "index.js", "server.js", "main.go", "main.rs",
            "Application.java", "Program.cs", "index.php"
        ]

        # Documentation files
        doc_patterns = ["README.md", "README.rst", "README.txt", "CHANGELOG.md", "CONTRIBUTING.md"]

        # Test files
        test_patterns = ["test_", "tests/", "spec_", "__init__.py"]

        all_patterns = config_patterns + entry_patterns + doc_patterns + test_patterns

        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                file_name = file_path.name
                relative_path = str(file_path.relative_to(project_path))

                # Check if file matches any pattern
                for pattern in all_patterns:
                    if pattern in file_name or pattern in relative_path:
                        key_files.append(relative_path)
                        break

        # Limit to top 20 key files
        return key_files[:20]

    def _update_project_relationships(self, current_project: Path):
        """Update relationships between projects"""
        current_project_str = str(current_project)
        current_info = self.projects[current_project_str]

        # Compare with all other projects
        for other_path, other_info in self.projects.items():
            if other_path == current_project_str:
                continue

            # Calculate relationship strength
            relationship = self._calculate_relationship(current_info, other_info)

            if relationship.strength > 0.3:  # Only store significant relationships
                # Check if relationship already exists
                existing_rel = None
                for rel in self.relationships:
                    if (rel.source_project == current_project_str and rel.target_project == other_path) or \
                       (rel.source_project == other_path and rel.target_project == current_project_str):
                        existing_rel = rel
                        break

                if existing_rel:
                    # Update existing relationship
                    existing_rel.strength = max(existing_rel.strength, relationship.strength)
                    existing_rel.shared_elements.extend(relationship.shared_elements)
                    existing_rel.shared_elements = list(set(existing_rel.shared_elements))
                else:
                    # Add new relationship
                    self.relationships.append(relationship)

        self._save_relationships()

    def _calculate_relationship(self, project1: ProjectInfo, project2: ProjectInfo) -> ProjectRelationship:
        """Calculate relationship strength between two projects"""
        shared_elements = []
        strength = 0.0

        # Technology overlap
        tech1 = set(project1.technologies)
        tech2 = set(project2.technologies)
        tech_overlap = tech1.intersection(tech2)

        if tech_overlap:
            strength += len(tech_overlap) * 0.2
            shared_elements.extend([f"tech:{tech}" for tech in tech_overlap])

        # Dependency overlap
        dep1 = set(project1.dependencies)
        dep2 = set(project2.dependencies)
        dep_overlap = dep1.intersection(dep2)

        if dep_overlap:
            strength += len(dep_overlap) * 0.3
            shared_elements.extend([f"dep:{dep}" for dep in dep_overlap])

        # Language overlap
