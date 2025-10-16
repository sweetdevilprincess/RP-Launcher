#!/usr/bin/env python3
"""
File Loading Strategies

Strategy pattern for flexible file loading.
Allows different loading strategies for different file types/tiers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import concurrent.futures

from src.automation.core import log_to_file
from src.automation.file_loading import FileLoader


class FileLoadingStrategy(ABC):
    """Base class for file loading strategies."""

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize strategy.

        Args:
            log_file: Optional log file
        """
        self.log_file = log_file

    @abstractmethod
    def get_files_to_load(self, rp_dir: Path, context: Dict) -> List[Path]:
        """
        Get list of files to load.

        Args:
            rp_dir: RP directory
            context: Loading context (response_count, message, etc.)

        Returns:
            List of file paths to load
        """
        pass

    @abstractmethod
    def should_load(self, context: Dict) -> bool:
        """
        Check if files should be loaded given the context.

        Args:
            context: Loading context

        Returns:
            True if files should be loaded
        """
        pass

    def load_file_safe(self, file_path: Path) -> tuple[Path, Optional[str], Optional[str]]:
        """
        Safely load a file.

        Args:
            file_path: File to load

        Returns:
            Tuple of (file_path, content, error_message)
        """
        if not file_path.exists():
            return file_path, None, "File not found"

        try:
            content = file_path.read_text(encoding='utf-8')
            return file_path, content, None
        except Exception as e:
            return file_path, None, str(e)

    def log(self, message: str) -> None:
        """Log a message."""
        if self.log_file:
            log_to_file(self.log_file, message)


class Tier1Strategy(FileLoadingStrategy):
    """Strategy for loading TIER_1 files (core RP files)."""

    def should_load(self, context: Dict) -> bool:
        """TIER_1 files are always loaded."""
        return True

    def get_files_to_load(self, rp_dir: Path, context: Dict) -> List[Path]:
        """Get TIER_1 files."""
        files = [
            rp_dir / "AUTHOR'S_NOTES.md",
            rp_dir / "STORY_GENOME.md",
            rp_dir / "NAMING_CONVENTIONS.md",
            rp_dir / "SCENE_NOTES.md",
            rp_dir / "state" / "current_state.md",
            rp_dir / "state" / "story_arc.md",
            rp_dir / "characters" / "{{user}}.md",
        ]

        # Find main character ({{char}})
        chars_dir = rp_dir / "characters"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.md"):
                if char_file.name != "{{user}}.md":
                    files.append(char_file)
                    break

        return files


class Tier2Strategy(FileLoadingStrategy):
    """Strategy for loading TIER_2 files (guidelines)."""

    def __init__(self, frequency: int = 10, log_file: Optional[Path] = None):
        """
        Initialize TIER_2 strategy.

        Args:
            frequency: Load every N responses
            log_file: Optional log file
        """
        super().__init__(log_file)
        self.frequency = frequency

    def should_load(self, context: Dict) -> bool:
        """Load every N responses."""
        response_count = context.get('response_count', 0)
        return response_count % self.frequency == 0 or response_count == 1

    def get_files_to_load(self, rp_dir: Path, context: Dict) -> List[Path]:
        """Get TIER_2 files."""
        config_dir = rp_dir.parent / "config" / "guidelines"

        files = [
            config_dir / "Timing.txt",
            config_dir / "Writing_Style_Guide.md",
            config_dir / "NPC_Interaction_Rules.md",
            config_dir / "POV_and_Writing_Checklist.md",
            config_dir / "Time_Tracking_Guide.md",
            config_dir / "Story Guidelines.md",
        ]

        # Add RP overview
        rp_name = rp_dir.name
        overview_file = rp_dir / f"{rp_name}.md"
        if overview_file.exists():
            files.append(overview_file)

        return files


class Tier3Strategy(FileLoadingStrategy):
    """Strategy for loading TIER_3 files (entity cards)."""

    def should_load(self, context: Dict) -> bool:
        """Always check for entities to load."""
        return True

    def get_files_to_load(self, rp_dir: Path, context: Dict) -> List[Path]:
        """Get TIER_3 entity files based on message analysis."""
        # This would use entity analysis from agents
        # For now, just return basic entity detection
        message = context.get('message', '')
        entities_dir = rp_dir / "entities"

        if not entities_dir.exists():
            return []

        files = []
        for entity_file in entities_dir.glob("*.md"):
            # Simple name matching (will be enhanced by agent analysis)
            entity_name = entity_file.stem.lower()
            if entity_name in message.lower():
                files.append(entity_file)

        return files


class EntityFileStrategy(FileLoadingStrategy):
    """Strategy for loading entity cards with special handling."""

    def __init__(self, entity_names: List[str], log_file: Optional[Path] = None):
        """
        Initialize entity file strategy.

        Args:
            entity_names: Names of entities to load
            log_file: Optional log file
        """
        super().__init__(log_file)
        self.entity_names = entity_names

    def should_load(self, context: Dict) -> bool:
        """Load if entities are specified."""
        return bool(self.entity_names)

    def get_files_to_load(self, rp_dir: Path, context: Dict) -> List[Path]:
        """Get entity files by name."""
        entities_dir = rp_dir / "entities"

        if not entities_dir.exists():
            return []

        files = []
        for name in self.entity_names:
            entity_file = entities_dir / f"{name}.md"
            if entity_file.exists():
                files.append(entity_file)

        return files


class StrategyBasedFileLoader:
    """
    File loader that uses strategies for flexible loading.

    Replaces monolithic FileLoader with composable strategies.
    """

    def __init__(self, rp_dir: Path, log_file: Optional[Path] = None,
                 max_workers: int = 8):
        """
        Initialize strategy-based loader.

        Args:
            rp_dir: RP directory
            log_file: Optional log file
            max_workers: Max parallel workers
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.max_workers = max_workers

        # Default strategies
        self.strategies: Dict[str, FileLoadingStrategy] = {
            'tier1': Tier1Strategy(log_file),
            'tier2': Tier2Strategy(frequency=10, log_file=log_file),
            'tier3': Tier3Strategy(log_file)
        }

    def register_strategy(self, name: str, strategy: FileLoadingStrategy) -> None:
        """
        Register a custom loading strategy.

        Args:
            name: Strategy name
            strategy: Strategy instance
        """
        self.strategies[name] = strategy

    def load_with_strategy(self, strategy_name: str,
                          context: Dict) -> Dict[str, str]:
        """
        Load files using a specific strategy.

        Args:
            strategy_name: Name of strategy to use
            context: Loading context

        Returns:
            Dict of {filename: content}
        """
        if strategy_name not in self.strategies:
            raise KeyError(f"Strategy '{strategy_name}' not registered")

        strategy = self.strategies[strategy_name]

        # Check if we should load
        if not strategy.should_load(context):
            self.log(f"[{strategy_name}] Skipping - condition not met")
            return {}

        # Get files to load
        files_to_load = strategy.get_files_to_load(self.rp_dir, context)

        if not files_to_load:
            self.log(f"[{strategy_name}] No files to load")
            return {}

        # Load files in parallel
        return self._load_files_parallel(files_to_load, strategy_name)

    def _load_files_parallel(self, files: List[Path],
                            strategy_name: str) -> Dict[str, str]:
        """
        Load files in parallel.

        Args:
            files: Files to load
            strategy_name: Strategy name for logging

        Returns:
            Dict of {filename: content}
        """
        result = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file loads
            future_to_path = {
                executor.submit(self._load_file_safe, file_path): file_path
                for file_path in files
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_path):
                file_path, content, error = future.result()

                if content is not None:
                    result[file_path.name] = content
                    self.log(f"[{strategy_name}] Loaded {file_path.name}")
                elif error == "File not found":
                    self.log(f"[{strategy_name}] File not found: {file_path.name}")
                else:
                    self.log(f"[{strategy_name}] Error loading {file_path.name}: {error}")

        return result

    def _load_file_safe(self, file_path: Path) -> tuple[Path, Optional[str], Optional[str]]:
        """Safely load a file."""
        if not file_path.exists():
            return file_path, None, "File not found"

        try:
            content = file_path.read_text(encoding='utf-8')
            return file_path, content, None
        except Exception as e:
            return file_path, None, str(e)

    def load_all(self, context: Dict) -> Dict[str, Dict[str, str]]:
        """
        Load all files using all registered strategies.

        Args:
            context: Loading context

        Returns:
            Dict of {strategy_name: {filename: content}}
        """
        results = {}

        for strategy_name in self.strategies:
            files = self.load_with_strategy(strategy_name, context)
            if files:
                results[strategy_name] = files

        return results

    def log(self, message: str) -> None:
        """Log a message."""
        if self.log_file:
            log_to_file(self.log_file, message)


# Backward compatibility adapter
class TierFileLoader:
    """
    Adapter for backward compatibility with existing code.

    Wraps StrategyBasedFileLoader with simplified interface.
    """

    def __init__(self, rp_dir: Path, log_file: Optional[Path] = None):
        """
        Initialize tier file loader.

        Args:
            rp_dir: RP directory
            log_file: Optional log file
        """
        self.loader = StrategyBasedFileLoader(rp_dir, log_file)

    def load_tier1_files(self) -> Dict[str, str]:
        """Load TIER_1 files."""
        return self.loader.load_with_strategy('tier1', {})

    def load_tier2_files(self) -> Dict[str, str]:
        """Load TIER_2 files."""
        # Use default frequency from strategy
        return self.loader.load_with_strategy('tier2', {'response_count': 0})

    def load_tier3_entities(self, message: str) -> List[Path]:
        """
        Load TIER_3 entity files.

        Args:
            message: User message for entity detection

        Returns:
            List of entity file paths
        """
        context = {'message': message}
        files_dict = self.loader.load_with_strategy('tier3', context)

        # Return paths instead of content
        entities_dir = self.loader.rp_dir / "entities"
        return [
            entities_dir / filename
            for filename in files_dict.keys()
        ]
