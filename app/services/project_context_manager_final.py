"""
Final Project Context Manager methods for Samoey Copilot
This file contains the remaining methods to complete the Project Context Manager
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Complete the remaining methods for ProjectContextManager

class ProjectContextManagerFinal:
    """
    Final methods for ProjectContextManager to complete functionality
    """

    def _calculate_relationship(self, project1, project2):
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
        lang1 = set(project1.main_languages)
        lang2 = set(project2.main_languages)
        lang_overlap = lang1.intersection(lang2)

        if lang_overlap:
            strength += len(lang_overlap) * 0.25
            shared_elements.extend([f"lang:{lang}" for lang in lang_overlap])

        # Architecture pattern overlap
        arch1 = set(project1.architecture_patterns)
        arch2 = set(project2.architecture_patterns)
        arch_overlap = arch1.intersection(arch2)

        if arch_overlap:
            strength += len(arch_overlap) * 0.15
            shared_elements.extend([f"arch:{arch}" for arch in arch_overlap])

        # Project type similarity
        if project1.project_type == project2.project_type:
            strength += 0.1
            shared_elements.append(f"type:{project1.project_type}")

        # Normalize strength
        strength = min(1.0, strength)

        # Determine relationship type
        relationship_type = "technological"
        if dep_overlap:
            relationship_type = "dependency"
        elif tech_overlap and len(tech_overlap) > 2:
            relationship_type = "shared_tech"
        elif arch_overlap:
            relationship_type = "similar_structure"

        return ProjectRelationship(
            source_project=project1.project_path,
            target_project=project2.project_path,
            relationship_type=relationship_type,
            strength=strength,
            shared_elements=shared_elements,
            discovered_date=datetime.now().isoformat()
        )

    def _save_projects(self):
        """Save projects data to file"""
        try:
            # Ensure directory exists
            self.projects_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict for JSON serialization
            projects_dict = {path: asdict(info) for path, info in self.projects.items()}

            with open(self.projects_path, 'w') as f:
                json.dump(projects_dict, f, indent=2)

            logger.info(f"Projects data saved to {self.projects_path}")
        except Exception as e:
            logger.error(f"Error saving projects data: {e}")

    def _save_relationships(self):
        """Save relationships data to file"""
        try:
            # Ensure directory exists
            self.relationships_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict for JSON serialization
            relationships_dict = [asdict(rel) for rel in self.relationships]

            with open(self.relationships_path, 'w') as f:
                json.dump(relationships_dict, f, indent=2)

            logger.info(f"Relationships data saved to {self.relationships_path}")
        except Exception as e:
            logger.error(f"Error saving relationships data: {e}")

    def get_project_context(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive context for a specific project"""
        project_path = str(Path(project_path).resolve())

        if project_path not in self.projects:
            return None

        project_info = self.projects[project_path]

        # Get related projects
        related_projects = []
        for rel in self.relationships:
            if rel.source_project == project_path:
                related_projects.append({
                    "project_path": rel.target_project,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "shared_elements": rel.shared_elements
                })
            elif rel.target_project == project_path:
                related_projects.append({
                    "project_path": rel.source_project,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "shared_elements": rel.shared_elements
                })

        # Build comprehensive context
        context = {
            "project_info": asdict(project_info),
            "related_projects": related_projects,
            "user_preferences": self.learning_engine.get_user_preferences(),
            "style_profile": self.style_analyzer.get_style_profile()
        }

        return context

    def get_projects_summary(self) -> Dict[str, Any]:
        """Get summary of all analyzed projects"""
        total_projects = len(self.projects)
        total_relationships = len(self.relationships)

        # Technology distribution
        all_technologies = []
        for project in self.projects.values():
            all_techn
