"""
Personal Knowledge Base for Samoey Copilot
Stores and manages learned concepts, patterns, and user preferences
"""

import os
import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import settings
from app.services.personal_learning import PersonalLearningEngine

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Types of knowledge entries"""
    CODE_SNIPPET = "code_snippet"
    SOLUTION = "solution"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    LEARNED_CONCEPT = "learned_concept"
    ERROR_RESOLUTION = "error_resolution"
    BEST_PRACTICE = "best_practice"

@dataclass
class KnowledgeEntry:
    """A single knowledge entry"""
    id: str
    knowledge_type: KnowledgeType
    title: str
    content: Dict[str, Any]
    tags: List[str]
    source: str  # Where this knowledge came from
    confidence: float  # How confident we are in this knowledge
    usage_count: int  # How often this has been used/referenced
    last_accessed: str
    created_at: str
    updated_at: str

@dataclass
class KnowledgeRelationship:
    """Relationship between knowledge entries"""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float

class PersonalKnowledgeBase:
    """
    Manages personal knowledge storage, retrieval, and learning
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.learning_engine = PersonalLearningEngine(user_id)
        self.user_data_dir = Path(settings.USER_DATA_DIR) / str(user_id)
        self.knowledge_base_path = self.user_data_dir / "knowledge_base.json"
        self.relationships_path = self.user_data_dir / "knowledge_relationships.json"

        # Initialize knowledge structures
        self.knowledge_entries = self._load_knowledge_base()
        self.relationships = self._load_relationships()
        self.knowledge_graph = self._build_knowledge_graph()

    def _load_knowledge_base(self) -> Dict[str, KnowledgeEntry]:
        """Load knowledge base from file"""
        if self.knowledge_base_path.exists():
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    data = json.load(f)
                    return {entry_id: KnowledgeEntry(**entry) for entry_id, entry in data.items()}
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")

        return {}

    def _load_relationships(self) -> List[KnowledgeRelationship]:
        """Load knowledge relationships from file"""
        if self.relationships_path.exists():
            try:
                with open(self.relationships_path, 'r') as f:
                    data = json.load(f)
                    return [KnowledgeRelationship(**rel) for rel in data]
            except Exception as e:
                logger.error(f"Error loading knowledge relationships: {e}")

        return []

    def _build_knowledge_graph(self) -> Dict[str, Set[str]]:
        """Build a knowledge graph for relationship traversal"""
        graph = defaultdict(set)

        for rel in self.relationships:
            graph[rel.source_id].add(rel.target_id)
            # Add reverse relationship for undirected traversal
            if rel.relationship_type in ["related_to", "similar_to", "uses"]:
                graph[rel.target_id].add(rel.source_id)

        return dict(graph)

    def add_knowledge(self, knowledge_type: KnowledgeType, title: str, content: Dict[str, Any],
                    source: str, tags: List[str] = None, confidence: float = 0.8) -> str:
        """
        Add a new knowledge entry to the knowledge base
        """
        entry_id = self._generate_knowledge_id(title, knowledge_type)

        if tags is None:
            tags = []

        knowledge_entry = KnowledgeEntry(
            id=entry_id,
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            tags=tags,
            source=source,
            confidence=confidence,
            usage_count=0,
            last_accessed=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.knowledge_entries[entry_id] = knowledge_entry

        # Auto-discover relationships
        self._discover_relationships(entry_id)

        # Save to disk
        self._save_knowledge_base()
        self._save_relationships()

        logger.info(f"Added knowledge entry: {title} ({knowledge_type.value})")
        return entry_id

    def _generate_knowledge_id(self, title: str, knowledge_type: KnowledgeType) -> str:
        """Generate a unique ID for a knowledge entry"""
        content = f"{title}_{knowledge_type.value}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _discover_relationships(self, entry_id: str):
        """Automatically discover relationships between knowledge entries"""
        current_entry = self.knowledge_entries[entry_id]

        # Find related entries based on tags and content similarity
        for other_id, other_entry in self.knowledge_entries.items():
            if other_id == entry_id:
                continue

            # Check tag similarity
            tag_similarity = len(set(current_entry.tags) & set(other_entry.tags))

            # Check content similarity (simplified)
            content_similarity = self._calculate_content_similarity(
                current_entry.content, other_entry.content
            )

            # Create relationship if similarity is high enough
            combined_similarity = tag_similarity * 0.3 + content_similarity * 0.7

            if combined_similarity > 0.5:
                relationship_type = "similar_to" if combined_similarity > 0.7 else "related_to"

                # Check if relationship already exists
                existing = any(
                    rel.source_id == entry_id and rel.target_id == other_id
                    for rel in self.relationships
                )

                if not existing:
                    relationship = KnowledgeRelationship(
                        source_id=entry_id,
                        target_id=other_id,
                        relationship_type=relationship_type,
                        strength=combined_similarity
                    )
                    self.relationships.append(relationship)

        # Update knowledge graph
        self.knowledge_graph = self._build_knowledge_graph()

    def _calculate_content_similarity(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> float:
        """Calculate similarity between two content dictionaries"""
        # Convert to strings for comparison
        str1 = str(content1).lower()
        str2 = str(content2).lower()

        # Extract words
        words1 = set(re.findall(r'\b\w+\b', str1))
        words2 = set(re.findall(r'\b\w+\b', str2))

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_relevant_knowledge(self, query: str, limit: int = 5,
                             knowledge_types: List[KnowledgeType] = None) -> List[KnowledgeEntry]:
        """
        Retrieve knowledge entries relevant to a query
        """
        if knowledge_types is None:
            knowledge_types = list(KnowledgeType)

        # Score all knowledge entries
        scored_entries = []
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))

        for entry_id, entry in self.knowledge_entries.items():
            if entry.knowledge_type not in knowledge_types:
                continue

            score = 0.0

            # Title matching (highest weight)
            if query_lower in entry.title.lower():
                score += 0.5

            # Tag matching
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 0.3

            # Content word matching
            entry_content = str(entry.content).lower()
            entry_words = set(re.findall(r'\b\w+\b', entry_content))

            if query_words & entry_words:
                word_overlap = len(query_words & entry_words)
                score += (word_overlap / len(query_words)) * 0.2

            # Boost frequently used entries
            score += min(entry.usage_count * 0.01, 0.1)

            # Boost by confidence
            score += entry.confidence * 0.1

            if score > 0:
                scored_entries.append((entry, score))

        # Sort by score and return top results
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        results = [entry for entry, score in scored_entries[:limit]]

        # Update usage counts
        for entry in results:
            entry.usage_count += 1
            entry.last_accessed = datetime.now().isoformat()

        # Save updated usage counts
        self._save_knowledge_base()

        return results

    def get_knowledge_by_type(self, knowledge_type: KnowledgeType) -> List[KnowledgeEntry]:
        """Get all knowledge entries of a specific type"""
        return [
            entry for entry in self.knowledge_entries.values()
            if entry.knowledge_type == knowledge_type
        ]

    def get_knowledge_by_tags(self, tags: List[str]) -> List[KnowledgeEntry]:
        """Get knowledge entries that have specific tags"""
        return [
            entry for entry in self.knowledge_entries.values()
            if any(tag in entry.tags for tag in tags)
        ]

    def find_related_knowledge(self, entry_id: str, depth: int = 2) -> List[KnowledgeEntry]:
        """Find knowledge entries related to a specific entry"""
        if entry_id not in self.knowledge_entries:
            return []

        related_entries = []
        visited = set([entry_id])
        current_level = [entry_id]

        for _ in range(depth):
            next_level = []

            for current_id in current_level:
                # Get direct neighbors from knowledge graph
                neighbors = self.knowledge_graph.get(current_id, set())

                for neighbor_id in neighbors:
                    if neighbor_id not in visited and neighbor_id in self.knowledge_entries:
                        visited.add(neighbor_id)
                        next_level.append(neighbor_id)
                        related_entries.append(self.knowledge_entries[neighbor_id])

            current_level = next_level

        return related_entries

    def update_knowledge(self, entry_id: str, content: Dict[str, Any] = None,
                        tags: List[str] = None, confidence: float = None) -> bool:
        """Update an existing knowledge entry"""
        if entry_id not in self.knowledge_entries:
            return False

        entry = self.knowledge_entries[entry_id]

        if content is not None:
            entry.content = content
        if tags is not None:
            entry.tags = tags
        if confidence is not None:
            entry.confidence = confidence

        entry.updated_at = datetime.now().isoformat()

        # Re-discover relationships since content changed
        self._remove_relationships(entry_id)
        self._discover_relationships(entry_id)

        # Save changes
        self._save_knowledge_base()
        self._save_relationships()

        return True

    def _remove_relationships(self, entry_id: str):
        """Remove all relationships involving a specific entry"""
        self.relationships = [
            rel for rel in self.relationships
            if rel.source_id != entry_id and rel.target_id != entry_id
        ]
        self.knowledge_graph = self._build_knowledge
