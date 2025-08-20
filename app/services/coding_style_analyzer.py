"""
Coding Style Analyzer for Samoey Copilot
Advanced analysis of user's coding patterns, style preferences, and architectural decisions
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
from dataclasses import dataclass

from app.core.config import settings
from app.services.personal_learning import PersonalLearningEngine

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Metrics for a single code file"""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    average_function_length: float
    complexity_score: float
    style_consistency: float

@dataclass
class StylePattern:
    """Detected coding style pattern"""
    pattern_type: str
    pattern_name: str
    frequency: int
    examples: List[str]
    confidence: float

class CodingStyleAnalyzer:
    """
    Advanced coding style analyzer that learns from user's code
    and provides intelligent style recommendations
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.learning_engine = PersonalLearningEngine(user_id)
        self.user_data_dir = Path(settings.USER_DATA_DIR) / str(user_id)
        self.analysis_results_path = self.user_data_dir / "style_analysis.json"

        # Load previous analysis results
        self.analysis_results = self._load_analysis_results()

    def _load_analysis_results(self) -> Dict[str, Any]:
        """Load previous analysis results"""
        if self.analysis_results_path.exists():
            try:
                with open(self.analysis_results_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading analysis results: {e}")

        return {
            "file_analyses": {},
            "style_patterns": [],
            "recommendations": [],
            "last_analysis": None
        }

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze an entire project for coding patterns and style
        """
        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        analysis_results = {
            "project_path": str(project_path),
            "files_analyzed": 0,
            "total_lines": 0,
            "style_patterns": [],
            "recommendations": [],
            "file_metrics": [],
            "project_complexity": "medium",
            "consistency_score": 0.0,
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Analyze all Python files in the project
        python_files = list(project_path.rglob("*.py"))
        file_metrics = []
        all_patterns = []

        for file_path in python_files:
            try:
                file_analysis = self.analyze_file(str(file_path))
                if file_analysis:
                    file_metrics.append(file_analysis)
                    all_patterns.extend(file_analysis.get("patterns", []))
                    analysis_results["files_analyzed"] += 1
                    analysis_results["total_lines"] += file_analysis.get("total_lines", 0)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")

        # Aggregate patterns and generate recommendations
        if file_metrics:
            analysis_results["file_metrics"] = file_metrics
            analysis_results["style_patterns"] = self._aggregate_patterns(all_patterns)
            analysis_results["recommendations"] = self._generate_recommendations(file_metrics, all_patterns)
            analysis_results["consistency_score"] = self._calculate_consistency_score(file_metrics)
            analysis_results["project_complexity"] = self._assess_project_complexity(file_metrics)

        # Update learning engine with project context
        project_info = {
            "type": "python_project",
            "technologies": self._extract_technologies(all_patterns),
            "dependencies": self._extract_dependencies(python_files),
            "complexity": analysis_results["project_complexity"]
        }
        self.learning_engine.add_project_context(str(project_path), project_info)

        # Save analysis results
        self._save_analysis_results(analysis_results)

        return analysis_results

    def analyze_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single file for coding style and patterns
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the code
            tree = ast.parse(content)

            # Calculate basic metrics
            metrics = self._calculate_file_metrics(file_path, content, tree)

            # Analyze patterns
            patterns = self._analyze_file_patterns(content, tree)

            # Check style consistency
            consistency_score = self._check_style_consistency(content, patterns)

            analysis = {
                "file_path": file_path,
                "metrics": metrics.__dict__,
                "patterns": [p.__dict__ for p in patterns],
                "consistency_score": consistency_score,
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Update learning engine with style analysis
            self.learning_engine.analyze_code_style(file_path, content)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None

    def _calculate_file_metrics(self, file_path: str, content: str, tree: ast.AST) -> CodeMetrics:
        """Calculate comprehensive metrics for a file"""
        lines = content.split('\n')
        total_lines = len(lines)

        # Count different types of lines
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1

        # Count functions and classes
        function_count = 0
        class_count = 0
        function_lengths = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1
                # Calculate function length (number of lines)
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    function_lengths.append(node.end_lineno - node.lineno + 1)
            elif isinstance(node, ast.ClassDef):
                class_count += 1

        # Calculate average function length
        avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0

        # Calculate complexity score (simplified cyclomatic complexity)
        complexity_score = self._calculate_complexity(tree)

        # Calculate style consistency
        style_consistency = self._check_style_consistency(content, [])

        return CodeMetrics(
            file_path=file_path,
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            average_function_length=avg_function_length,
            complexity_score=complexity_score,
            style_consistency=style_consistency
        )

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity score"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _analyze_file_patterns(self, content: str, tree: ast.AST) -> List[StylePattern]:
        """Analyze coding patterns in a file"""
        patterns = []

        # Naming convention patterns
        patterns.extend(self._analyze_naming_patterns(tree))

        # Import patterns
        patterns.extend(self._analyze_import_patterns(tree))

        # Error handling patterns
        patterns.extend(self._analyze_error_handling_patterns(tree))

        # Documentation patterns
        patterns.extend(self._analyze_documentation_patterns(content, tree))

        # Code structure patterns
        patterns.extend(self._analyze_structure_patterns(tree))

        return patterns

    def _analyze_naming_patterns(self, tree: ast.AST) -> List[StylePattern]:
        """Analyze naming convention patterns"""
        patterns = []

        variable_names = []
        function_names = []
        class_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variable_names.append(node.id)
            elif isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                class_names.append(node.name)

        # Analyze naming patterns
        if variable_names:
            variable_style = self._detect_naming_style(variable_names)
            patterns.append(StylePattern(
                pattern_type="naming_convention",
                pattern_name=f"variable_naming_{variable_style}",
                frequency=len([n for n in variable_names if self._matches_naming_style(n, variable_style)]),
                examples=variable_names[:3],
                confidence=0.8
            ))

        if function_names:
            function_style = self._detect_naming_style(function_names)
            patterns.append(StylePattern(
                pattern_type="naming_convention",
                pattern_name=f"function_naming_{function_style}",
                frequency=len([n for n in function_names if self._matches_naming_style(n, function_style)]),
                examples=function_names[:3],
                confidence=0.8
            ))

        if class_names:
            class_style = self._detect_naming_style(class_names)
            patterns.append(StylePattern(
                pattern_type="naming_convention",
                pattern_name=f"class_naming_{class_style}",
                frequency=len([n for n in class_names if self._matches_naming_style(n, class_style)]),
                examples=class_names[:3],
                confidence=0.9
            ))

        return patterns

    def _detect_naming_style(self, names: List[str]) -> str:
        """Detect the naming style from a list of names"""
        if not names:
            return "unknown"

        camel_count = sum(1 for name in names if re.match(r'^[a-z][a-zA-Z0-9]*$', name))
        snake_count = sum(1 for name in names if re.match(r'^[a-z][a-z0-9_]*$', name))
        pascal_count = sum(1 for name in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        upper_count = sum(1 for name in names if re.match(r'^[A-Z][A-Z0-9]*$', name))

        if camel_count > snake_count and camel_count > pascal_count and camel_count > upper_count:
            return "camelCase"
        elif snake_count > camel_count and snake_count > pascal_count and snake_count > upper_count:
            return "snake_case"
        elif pascal_count > camel_count and pascal_count > snake_count and pascal_count > upper_count:
            return "PascalCase"
        elif upper_count > camel_count and upper_count > snake_count and upper_count > pascal_count:
            return "UPPER_CASE"
        else:
            return "mixed"

    def _matches_naming_style(self, name: str, style: str) -> bool:
        """Check if a name matches a specific naming style"""
        if style == "camelCase":
            return re.match(r'^[a-z][a-zA-Z0-9]*$', name) is not None
        elif style == "snake_case":
            return re.match(r'^[a-z][a-z0-9_]*$', name) is not None
        elif style == "PascalCase":
            return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
        elif style == "UPPER_CASE":
            return re.match(r'^[A-Z][A-Z0-9]*$', name) is not None
        return False

    def _analyze_import_patterns(self, tree: ast.AST) -> List[StylePattern]:
        """Analyze import organization patterns"""
        patterns = []

        imports = []
        from_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    from_imports.append(node.module)

        # Check for import organization
        if imports:
            patterns.append(StylePattern(
                pattern_type="import_style",
                pattern_name="standard_imports",
                frequency=len(imports),
                examples=imports[:3],
                confidence=0.9
            ))

        if from_imports:
            patterns.append(StylePattern(
                pattern_type="import_style",
                pattern_name="from_imports",
                frequency=len(from_imports),
                examples=from_imports[:3],
                confidence=0.9
            ))

        return patterns

    def _analyze_error_handling_patterns(self, tree: ast.AST) -> List[StylePattern]:
        """Analyze error handling patterns"""
        patterns = []

        try_blocks = []
        logging_calls = []
        assert_statements = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                try_blocks.append(node)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["print", "logging", "logger"]:
                        logging_calls.append(node)
            elif isinstance(node, ast.Assert):
                assert_statements.append(node)

        if try_blocks:
            patterns.append(StylePattern(
                pattern_type="error_handling",
                pattern_name="try_except_blocks",
                frequency=len(try_blocks),
                examples=["try/except block"],
                confidence=0.9
            ))

        if logging_calls:
            patterns.append(StylePattern(
                pattern_type="error_handling",
                pattern_name="logging_usage",
                frequency=len(logging_calls),
                examples=["logging call"],
                confidence=0.8
            ))

        if assert_statements:
            patterns.append(StylePattern(
                pattern_type="error_handling",
                pattern_name="assert_usage",
                frequency=len(assert_statements),
                examples=["assert statement"],
                confidence=0.7
            ))

        return patterns

    def _analyze_documentation_patterns(self, content: str, tree: ast.AST) -> List[StylePattern]:
        """Analyze documentation patterns"""
        patterns = []

        docstrings = []
        comment_lines = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if ast.get_docstring(node):
                    docstrings.append(ast.get_docstring(node))

        # Count comment lines
        comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]

        if docstrings:
            patterns.append(StylePattern(
                pattern_type="documentation",
                pattern_name="docstring_usage",
                frequency=len(docstrings),
                examples=docstrings[:1],
                confidence=0.9
            ))

        if comment_lines:
            patterns.append(StylePattern(
                pattern_type="documentation",
                pattern_name="inline_comments",
                frequency=len(comment_lines),
                examples=comment_lines[:3],
                confidence=0.8
            ))

        return patterns

    def _analyze_structure_patterns(self, tree: ast.AST) -> List[StylePattern]:
        """Analyze code structure patterns"""
        patterns = []

        classes = []
        functions = []
        methods = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
            elif isinstance(node, ast.FunctionDef):
                # Check if it's a method (inside a class)
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and node in list(ast.iter_child_nodes(parent)):
                        methods.append(node)
                        break
                else:
                    functions.append(node)

        if classes:
            patterns.append(StylePattern(
                pattern_type="structure",
                pattern_name="class_usage",
                frequency=len(classes),
                examples=[c.name for c in classes[:3]],
                confidence=0.9
            ))

        if functions:
            patterns.append(StylePattern(
                pattern_type="structure",
                pattern_name="function_usage",
                frequency=len(functions),
                examples=[f.name for f in functions[:3]],
                confidence=0.9
            ))

        if methods:
            patterns.append(StylePattern(
                pattern_type="structure",
                pattern_name="method_usage",
                frequency=len(methods),
                examples=[m.name for m in methods[:3]],
                confidence=0.9
            ))

        return patterns

    def _check_style_consistency(self, content: str, patterns: List[StylePattern]) -> float:
        """Check how consistent the coding style is"""
        # This is a simplified consistency check
        # In a real implementation, this would be much more sophisticated

        consistency_score = 0.8  # Base score

        # Check indentation consistency
        lines = content.split('\n')
        indent_sizes = []
        for line in lines:
            if line.strip():  # Non-empty line
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indent_sizes.append(leading_spaces)

        if indent_sizes:
            most_common_indent = max(set(indent_sizes), key=indent_sizes.count)
            indent_consistency = sum(1 for size in indent_sizes if size == most_common_indent) / len(indent_sizes)
            consistency_score *= indent_consistency

        # Check naming consistency
        pattern_types = {}
        for pattern in patterns:
            if pattern.pattern_type == "naming_convention":
                pattern_types[pattern.pattern_name] = pattern.frequency

        # Reduce score if multiple naming styles are used
        if len(pattern_types) > 2:
            consistency_score *= 0.7

        return min(1.0, max(0.0, consistency_score))

    def _aggregate_patterns(self, all_patterns: List[StylePattern]) -> List[Dict[str, Any]]:
        """Aggregate patterns from multiple files"""
        pattern_counts = defaultdict(lambda: {"frequency": 0, "examples": [], "confidence": 0})

        for pattern in all_patterns:
            key = f"{pattern.pattern_type}_{pattern.pattern_name}"
            pattern_counts[key]["frequency"] += pattern.frequency
            pattern_counts[key]["examples"].extend(pattern.examples)
            pattern_counts[key]["confidence"] = max(pattern_counts[key]["confidence"], pattern.confidence)

        # Convert to list and sort by frequency
        aggregated = []
        for key, data in pattern_counts.items():
            pattern_type, pattern_name = key.split('_', 1)
            aggregated.append({
                "pattern_type": pattern_type,
                "pattern_name": pattern_name,
                "frequency": data["frequency"],
                "examples": list(set(data["examples"]))[:5],  # Unique examples, max 5
                "confidence": data["confidence"]
            })

        return sorted(aggregated, key=lambda x: x["frequency"], reverse=True)

    def _generate_recommendations(self, file_metrics: List[Dict], patterns: List[StylePattern]) -> List[Dict[str, Any]]:
        """Generate style recommendations based on analysis"""
        recommendations = []

        # Analyze function lengths
        avg_function_lengths = []
        for metric in file_metrics:
            if "metrics" in metric:
                avg_function_lengths.append(metric["metrics"].get("average_function_length", 0))

        if avg_function_lengths:
            avg_length = sum(avg_function_lengths) / len(avg_function_lengths)
            if avg_length > 20:
                recommendations.append({
                    "type": "refactoring",
                    "priority": "medium",
                    "title": "Consider breaking down large functions",
                    "description": f"Average function length is {avg_length:.1f} lines. Consider breaking down functions larger than 20 lines.",
                    "confidence": 0.7
                })

        # Analyze complexity scores
        complexity_scores = []
        for metric in file_metrics:
            if "metrics" in metric:
                complexity_scores.append(metric["metrics"].get("complexity_score", 0))

        if complexity_scores:
            avg_complexity = sum(complexity_scores) / len(complexity_scores)
            if avg_complexity > 10:
                recommendations.append({
                    "type": "complexity",
                    "priority": "high",
                    "title": "High code complexity detected",
                    "description": f"Average cyclomatic complexity is {avg_complexity:.1f}. Consider refactoring complex functions.",
                    "confidence": 0.8
                })

        # Analyze documentation
        docstring_patterns = [p for p in patterns if p.pattern_type == "documentation" and p.pattern_name == "docstring_usage"]
        if not docstring_patterns or docstring_patterns[0].frequency < len(file_metrics) * 0.5:
            recommendations.append({
                "type": "documentation",
                "priority": "medium",
                "title": "Consider adding more docstrings",
                "description": "Less than 50% of functions/classes have docstrings. Consider adding documentation for better code maintainability.",
                "confidence": 0.9
            })

        # Analyze error handling
        error_patterns = [p for p in patterns if p.pattern_type == "error_handling" and p.pattern_name == "try_except_blocks"]
        if not error_patterns or error_patterns[0].frequency < len(file_metrics) * 0.3:
            recommendations.append({
                "type": "error_handling",
                "priority": "low",
                "title": "Consider adding more error handling",
                "description": "Limited error handling detected. Consider adding try/except blocks for better robustness.",
                "confidence": 0.6
            })

        return recommendations

    def _calculate_consistency_score(self, file_metrics: List[Dict]) -> float:
        """Calculate overall consistency score across files"""
        if not file_metrics:
            return 0.0

        consistency_scores = []
        for metric in file_metrics:
            if "metrics" in metric:
                consistency_scores.append(metric["metrics"].get("style_consistency", 0.0))

        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0

    def _assess_project_complexity(self, file_metrics: List[Dict]) -> str:
        """Assess overall project complexity"""
        if not file_metrics:
            return "unknown"

        avg_complexity = 0
        total_lines = 0
        total_functions = 0

        for metric in file_metrics:
            if "metrics" in metric:
                metrics_data = metric["metrics"]
                avg_complexity += metrics_data.get("complexity_score", 0)
                total_lines += metrics_data.get("total_lines", 0)
                total_functions += metrics_data.get("function_count", 0)

        if len(file_metrics) > 0:
            avg_complexity /= len(file_metrics)

        if total_lines < 1000 and avg_complexity < 5:
            return "low"
        elif total_lines < 5000 and avg_complexity < 15:
            return "medium"
        else:
            return "high"

    def _extract_technologies(self, patterns: List[StylePattern]) -> List[str]:
        """Extract technologies used based on patterns"""
        technologies = []

        # Look for specific import patterns that indicate technologies
        for pattern in patterns:
            if pattern.pattern_type == "import_style":
                for example in
"""
Coding Style Analyzer for Samoey Copilot
Advanced analysis of user's coding patterns, style preferences, and architectural decisions
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
from dataclasses import dataclass

from app.core.config import settings
from app.services.personal_learning import PersonalLearningEngine

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Metrics for a single code file"""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    average_function_length: float
    complexity_score: float
    style_consistency: float

@dataclass
class StylePattern:
    """Detected coding style pattern"""
    pattern_type: str
    pattern_name: str
    frequency: int
    examples: List[str]
    confidence: float

class CodingStyleAnalyzer:
    """
    Advanced coding style analyzer that learns from user's code
    and provides intelligent style recommendations
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.learning_engine = PersonalLearningEngine(user_id)
        self.user_data_dir = Path(settings.USER_DATA_DIR) / str(user_id)
        self.analysis_results_path = self.user_data_dir / "style_analysis.json"

        # Load previous analysis results
        self.analysis_results = self._load_analysis_results()

    def _load_analysis_results(self) -> Dict[str, Any]:
        """Load previous analysis results"""
        if self.analysis_results_path.exists():
            try:
                with open(self.analysis_results_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading analysis results: {e}")

        return {
            "file_analyses": {},
            "style_patterns": [],
            "recommendations": [],
            "last_analysis": None
        }

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze an entire project for coding patterns and style
        """
        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        analysis_results = {
            "project_path": str(project_path),
            "files_analyzed": 0,
            "total_lines": 0,
            "style_patterns": [],
            "recommendations": [],
            "file_metrics": [],
            "project_complexity": "medium",
            "consistency_score": 0.0,
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Analyze all Python files in the project
        python_files = list(project_path.rglob("*.py"))
        file_metrics = []
        all_patterns = []

        for file_path in python_files:
            try:
                file_analysis = self.analyze_file(str(file_path))
                if file_analysis:
                    file_metrics.append(file_analysis)
                    all_patterns.extend(file_analysis.get("patterns", []))
                    analysis_results["files_analyzed"] += 1
                    analysis_results["total_lines"] += file_analysis.get("total_lines", 0)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")

        # Aggregate patterns and generate recommendations
        if file_metrics:
            analysis_results["file_metrics"] = file_metrics
            analysis_results["style_patterns"] = self._aggregate_patterns(all_patterns)
            analysis_results["recommendations"] = self._generate_recommendations(file_metrics, all_patterns)
            analysis_results["consistency_score"] = self._calculate_consistency_score(file_metrics)
            analysis_results["project_complexity"] = self._assess_project_complexity(file_metrics)

        # Update learning engine with project context
        project_info = {
            "type": "python_project",
            "technologies": self._extract_technologies(all_patterns),
            "dependencies": self._extract_dependencies(python_files),
            "complexity": analysis_results["project_complexity"]
        }
        self.learning_engine.add_project_context(str(project_path), project_info)

        # Save analysis results
        self._save_analysis_results(analysis_results)

        return analysis_results

    def analyze_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single file for coding style and patterns
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the code
            tree = ast.parse(content)

            # Calculate basic metrics
            metrics = self._calculate_file_metrics(file_path, content, tree)

            # Analyze patterns
            patterns = self._analyze_file_patterns(content, tree)

            # Check style consistency
            consistency_score = self._check_style_consistency(content, patterns)

            analysis = {
                "file_path": file_path,
                "metrics": metrics.__dict__,
                "patterns": [p.__dict__ for p in patterns],
                "consistency_score": consistency_score,
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Update learning engine with style analysis
            self.learning_engine.analyze_code_style(file_path, content)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None

    def _calculate_file_metrics(self, file_path: str, content: str, tree: ast.AST) -> CodeMetrics:
        """Calculate comprehensive metrics for a file"""
        lines = content.split('\n')
        total_lines = len(lines)

        # Count different types of lines
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1

        # Count functions and classes
        function_count = 0
        class_count = 0
        function_lengths = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1
                # Calculate function length (number of lines)
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    function_lengths.append(node.end_lineno - node.lineno + 1)
            elif isinstance(node, ast.ClassDef):
                class_count += 1

        # Calculate average function length
        avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0

        # Calculate complexity score (simplified cyclomatic complexity)
        complexity_score = self._calculate_complexity(tree)

        # Calculate style consistency
        style_consistency = self._check_style_consistency(content, [])

        return CodeMetrics(
            file_path=file_path,
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            average_function_length=avg_function_length,
            complexity_score=complexity_score,
            style_consistency=style_consistency
        )

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity score"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _analyze_file_patterns(self, content: str, tree: ast.AST) -> List[StylePattern]:
        """Analyze coding patterns in a file"""
        patterns = []

        # Naming convention patterns
        patterns.extend(self._analyze_naming_patterns(tree))

        # Import patterns
        patterns.extend(self._analyze_import_patterns(tree))

        # Error handling patterns
        patterns.extend(self._analyze_error_handling_patterns(tree))

        # Documentation patterns
        patterns.extend(self._analyze_documentation_patterns(content, tree))

        # Code structure patterns
        patterns.extend(self._analyze_structure_patterns(tree))

        return patterns

    def _analyze_naming_patterns(self, tree: ast.AST) -> List[StylePattern]:
        """Analyze naming convention patterns"""
        patterns = []

        variable_names = []
        function_names = []
        class_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variable_names.append(node.id)
            elif isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                class_names.append(node.name)

        # Analyze naming patterns
        if variable_names:
            variable_style = self._detect_naming_style(variable_names)
            patterns.append(StylePattern(
                pattern_type="naming_convention",
                pattern_name=f"variable_naming_{variable_style}",
                frequency=len([n for n in variable_names if self._matches_naming_style(n, variable_style)]),
                examples=variable_names[:3],
                confidence=0.8
            ))

        if function_names:
            function_style = self._detect_naming_style(function_names)
            patterns.append(StylePattern(
                pattern_type="naming_convention",
                pattern_name=f"function_naming_{function_style}",
                frequency=len([n for n in function_names if self._matches_naming_style(n, function_style)]),
                examples=function_names[:3],
                confidence=0.8
            ))

        if class_names:
            class_style = self._detect_naming_style(class_names)
            patterns.append(StylePattern(
                pattern_type="naming_con
