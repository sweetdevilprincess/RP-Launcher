#!/usr/bin/env python3
"""
File Loading Module

Handles tiered file loading system:
- TIER_1: Core RP files (loaded every response)
- TIER_2: Guidelines (loaded periodically)
- TIER_3: Conditional files (loaded based on triggers)
- Proxy: Optional proxy prompt injection
"""

from pathlib import Path
from typing import Dict, Optional
import concurrent.futures

from src.automation.core import log_to_file


class FileLoader:
    """Handles tiered file loading"""

    def __init__(self, rp_dir: Path, log_file: Path, max_workers: int = 8):
        """Initialize file loader

        Args:
            rp_dir: RP directory path
            log_file: Path to log file
            max_workers: Max parallel workers for file loading
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.max_workers = max_workers

    def _load_file_safe(self, file_path: Path) -> tuple[Path, Optional[str], Optional[str]]:
        """Safely load a file (helper for parallel loading)

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

    def load_tier1_files(self) -> Dict[str, str]:
        """Load TIER_1 files (core RP files loaded every response)

        Returns:
            Dict of {filename: content}
        """
        tier1_files = {}

        # Core RP files (always load)
        files_to_load = [
            self.rp_dir / "AUTHOR'S_NOTES.md",
            self.rp_dir / "STORY_GENOME.md",
            self.rp_dir / "SCENE_NOTES.md",
            self.rp_dir / "state" / "current_state.md",
            self.rp_dir / "state" / "story_arc.md",
            self.rp_dir / "characters" / "{{user}}.md",
        ]

        # Find main character ({{char}}) - first character file that's not {{user}}
        chars_dir = self.rp_dir / "characters"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.md"):
                if char_file.name != "{{user}}.md":
                    files_to_load.append(char_file)
                    break  # Only load the first main character

        # Load all files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file loads
            future_to_path = {
                executor.submit(self._load_file_safe, file_path): file_path
                for file_path in files_to_load
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                file_path, content, error = future.result()

                if content is not None:
                    tier1_files[file_path.name] = content
                    log_to_file(self.log_file, f"TIER_1: Loaded {file_path.name}")
                elif error == "File not found":
                    log_to_file(self.log_file, f"TIER_1: File not found: {file_path.name}")
                else:
                    log_to_file(self.log_file, f"WARNING: Could not load TIER_1 file {file_path.name}: {error}")

        return tier1_files

    def load_tier2_files(self, response_count: int) -> Dict[str, str]:
        """Load TIER_2 files (guidelines loaded every 4th response)

        Args:
            response_count: Current response count

        Returns:
            Dict of {filename: content}
        """
        tier2_files = {}

        # Only load on 4th responses
        if response_count % 4 != 0:
            return tier2_files

        log_to_file(self.log_file, f"TIER_2: Loading (response {response_count} is divisible by 4)")

        # Guidelines and reference files
        files_to_load = [
            self.rp_dir.parent / "config" / "guidelines" / "Timing.txt",
            self.rp_dir.parent / "config" / "guidelines" / "Writing_Style_Guide.md",
            self.rp_dir.parent / "config" / "guidelines" / "NPC_Interaction_Rules.md",
            self.rp_dir.parent / "config" / "guidelines" / "POV_and_Writing_Checklist.md",
            self.rp_dir.parent / "config" / "guidelines" / "Time_Tracking_Guide.md",
            self.rp_dir.parent / "config" / "guidelines" / "Story Guidelines.md",
        ]

        # Also load RP overview
        rp_name = self.rp_dir.name
        overview_file = self.rp_dir / f"{rp_name}.md"
        if overview_file.exists():
            files_to_load.append(overview_file)

        # Load all files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file loads
            future_to_path = {
                executor.submit(self._load_file_safe, file_path): file_path
                for file_path in files_to_load
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                file_path, content, error = future.result()

                if content is not None:
                    tier2_files[file_path.name] = content
                    log_to_file(self.log_file, f"TIER_2: Loaded {file_path.name}")
                elif error != "File not found":  # Don't log "not found" for optional files
                    log_to_file(self.log_file, f"WARNING: Could not load TIER_2 file {file_path.name}: {error}")

        return tier2_files

    def load_proxy_prompt(self) -> Optional[str]:
        """Load proxy prompt from proxy_prompt.txt

        Returns:
            Proxy prompt text or None if not found or empty
        """
        proxy_file = self.rp_dir.parent / "config" / "proxy_prompt.txt"

        if not proxy_file.exists():
            return None

        try:
            content = proxy_file.read_text(encoding='utf-8').strip()
            # Filter out comment lines and empty lines
            lines = [line for line in content.split('\n')
                     if line.strip() and not line.strip().startswith('#')]
            filtered_content = '\n'.join(lines).strip()

            return filtered_content if filtered_content else None
        except Exception as e:
            log_to_file(self.log_file, f"WARNING: Error loading proxy prompt: {e}")
            return None


# Convenience functions for backward compatibility
def load_tier1_files(rp_dir: Path, log_file: Path) -> Dict[str, str]:
    """Load TIER_1 files (convenience function)

    Args:
        rp_dir: RP directory path
        log_file: Path to log file

    Returns:
        Dict of {filename: content}
    """
    loader = FileLoader(rp_dir, log_file)
    return loader.load_tier1_files()


def load_tier2_files(rp_dir: Path, response_count: int, log_file: Path) -> Dict[str, str]:
    """Load TIER_2 files (convenience function)

    Args:
        rp_dir: RP directory path
        response_count: Current response count
        log_file: Path to log file

    Returns:
        Dict of {filename: content}
    """
    loader = FileLoader(rp_dir, log_file)
    return loader.load_tier2_files(response_count)


def load_proxy_prompt(base_dir: Path) -> Optional[str]:
    """Load proxy prompt (convenience function)

    Args:
        base_dir: Base directory (RP Claude Code root)

    Returns:
        Proxy prompt text or None
    """
    # For convenience function, we need to construct paths differently
    proxy_file = base_dir / "config" / "proxy_prompt.txt"

    if not proxy_file.exists():
        return None

    try:
        content = proxy_file.read_text(encoding='utf-8').strip()
        lines = [line for line in content.split('\n')
                 if line.strip() and not line.strip().startswith('#')]
        filtered_content = '\n'.join(lines).strip()

        return filtered_content if filtered_content else None
    except Exception as e:
        print(f"⚠️  Error loading proxy prompt: {e}")
        return None
