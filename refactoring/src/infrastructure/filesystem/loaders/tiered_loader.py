"""Data-driven tiered file loading for RP automation."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ....shared.interfaces import LoggingService
from ..markdown_store import MarkdownStore
from ..state_paths import StatePaths

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "tiered_bundles.json"


@dataclass(frozen=True)
class BundleDefinition:
    """Configuration definition for a tiered bundle."""

    id: str
    label: str
    trigger: Mapping[str, Any]
    entries: Sequence[Mapping[str, Any]]


@dataclass(frozen=True)
class TieredLoadResult:
    """Loaded files and metadata for a bundle."""

    bundle_id: str
    label: str
    files: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)


class TieredFileLoader:
    """Loads tiered RP artefacts (Tier1/2/3) using data-driven bundles."""

    def __init__(
        self,
        *,
        paths: StatePaths,
        markdown_store: MarkdownStore,
        logger: LoggingService,
        config: Mapping[str, Any],
    ) -> None:
        self.paths = paths
        self._markdown_store = markdown_store
        self.logger = logger
        self._bundles: list[BundleDefinition] = [
            BundleDefinition(
                id=bundle.get("id"),
                label=bundle.get("label", bundle.get("id", "")),
                trigger=bundle.get("trigger", {}),
                entries=bundle.get("entries", []),
            )
            for bundle in config.get("bundles", [])
            if bundle.get("id")
        ]
        self._base_paths: dict[str, Path] = {
            "rp": self.paths.rp_dir,
            "state": self.paths.state_dir,
            "config": (self.paths.rp_dir.parent / "config"),
        }
        self._config_store = MarkdownStore(root=self._base_paths["config"], logger=logger)

    @classmethod
    def from_default_config(
        cls,
        *,
        paths: StatePaths,
        markdown_store: MarkdownStore,
        logger: LoggingService,
        config_path: Path | None = None,
    ) -> TieredFileLoader:
        """Instantiate loader using the shared JSON configuration."""

        path = config_path or DEFAULT_CONFIG_PATH
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                config = json.load(handle)
        else:
            logger.warning(
                "tiered_loader.config_missing",
                context={"path": str(path)},
            )
            config = {"bundles": []}
        return cls(paths=paths, markdown_store=markdown_store, logger=logger, config=config)

    # ------------------------------------------------------------------
    # Public API

    def load_all(
        self,
        *,
        response_count: int | None,
        triggered_files: Sequence[Path] | None = None,
    ) -> dict[str, TieredLoadResult]:
        """Load all applicable bundles and return them keyed by bundle id."""

        results: dict[str, TieredLoadResult] = {}
        for bundle in self._bundles:
            if not self._trigger_applies(
                bundle.trigger,
                response_count=response_count,
                triggered_files=triggered_files,
            ):
                continue
            result = self._collect_bundle(bundle, triggered_files=triggered_files or [])
            if result is None:
                continue
            results[result.bundle_id] = result
        return results

    def load_tier1(self) -> dict[str, TieredLoadResult]:
        """Return bundles that are always included (Tier 1)."""

        return self._load_bundles({"always"})

    def load_tier2(self, *, response_count: int) -> dict[str, TieredLoadResult]:
        """Return periodic bundles for the given response count (Tier 2)."""

        return self._load_bundles({"every_n_responses"}, response_count=response_count)

    def load_tier3(self, *, triggered_files: Sequence[Path]) -> dict[str, TieredLoadResult]:
        """Return bundles driven by trigger-selected files (Tier 3)."""

        return self._load_bundles({"triggered"}, triggered_files=triggered_files)

    def load_tier3_referenced(self, *, triggered_files: Sequence[Path]) -> dict[str, TieredLoadResult]:
        """Return bundles for referenced entities (basics only)."""

        return self._load_bundles({"triggered_basics"}, triggered_files=triggered_files)

    # ------------------------------------------------------------------
    # Internal helpers

    def _load_bundles(
        self,
        trigger_types: set[str],
        *,
        response_count: int | None = None,
        triggered_files: Sequence[Path] | None = None,
    ) -> dict[str, TieredLoadResult]:
        results: dict[str, TieredLoadResult] = {}
        for bundle in self._bundles:
            trigger_type = bundle.trigger.get("type", "always")
            if trigger_type not in trigger_types:
                continue
            if not self._trigger_applies(
                bundle.trigger, response_count=response_count, triggered_files=triggered_files
            ):
                continue
            result = self._collect_bundle(bundle, triggered_files=triggered_files or [])
            if result is not None:
                results[result.bundle_id] = result
        return results

    def _trigger_applies(
        self,
        trigger: Mapping[str, Any],
        *,
        response_count: int | None,
        triggered_files: Sequence[Path] | None,
    ) -> bool:
        trigger_type = trigger.get("type", "always")
        if trigger_type == "always":
            return True
        if trigger_type == "every_n_responses":
            interval = int(trigger.get("interval", 1))
            if interval <= 0:
                self.logger.warning(
                    "tiered_loader.invalid_interval",
                    context={"interval": interval},
                )
                return False
            if response_count is None:
                return False
            return response_count % interval == 0
        if trigger_type in ("triggered", "triggered_basics"):
            return bool(triggered_files)
        self.logger.warning(
            "tiered_loader.unknown_trigger",
            context={"trigger_type": trigger_type},
        )
        return False

    def _collect_bundle(
        self,
        bundle: BundleDefinition,
        *,
        triggered_files: Sequence[Path],
    ) -> TieredLoadResult | None:
        files: dict[str, str] = {}
        loaded_paths: list[str] = []
        entity_metadata: dict[str, Any] = {
            "entities_with_cores": [],
            "entity_files": [],
        }
        for entry in bundle.entries:
            collected = self._resolve_entry(entry, triggered_files=triggered_files)
            for display_key, path, content, entry_meta in collected:
                if display_key in files:
                    continue
                files[display_key] = content
                loaded_paths.append(str(path))
                if entry_meta:
                    self._merge_metadata(entity_metadata, entry_meta)
        if not files:
            return None
        metadata: dict[str, Any] = {
            "loaded_paths": loaded_paths,
            "entry_count": len(files),
        }
        if entity_metadata["entities_with_cores"]:
            metadata["entities_with_cores"] = entity_metadata["entities_with_cores"]
        if entity_metadata["entity_files"]:
            metadata["entity_files"] = entity_metadata["entity_files"]
        return TieredLoadResult(
            bundle_id=bundle.id,
            label=bundle.label,
            files=files,
            metadata=metadata,
        )

    def _merge_metadata(self, target: dict[str, Any], entry_meta: dict[str, Any]) -> None:
        for key, value in entry_meta.items():
            if key == "entities_with_cores":
                existing = target.setdefault("entities_with_cores", [])
                for item in value:
                    if item not in existing:
                        existing.append(item)
            elif key == "entity_file":
                files = target.setdefault("entity_files", [])
                if value not in files:
                    files.append(value)

    def _resolve_entry(
        self,
        entry: Mapping[str, Any],
        *,
        triggered_files: Sequence[Path],
    ) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
        entry_type = entry.get("type", "path")
        if entry_type == "path":
            value = entry.get("value")
            if not value:
                return []
            base_key = entry.get("base", "rp")
            base_path = self._base_paths.get(base_key)
            if base_path is None:
                self.logger.warning(
                    "tiered_loader.unknown_base",
                    context={"base": base_key, "value": value},
                )
                return []
            path_value = Path(value)
            content, meta = self._read_from_base(base_key, path_value)
            if content is None:
                return []
            target = (base_path / path_value).resolve()
            return [(self._display_key(target), target, content, meta)]

        if entry_type == "main_character":
            return self._load_main_character()

        if entry_type == "rp_overview":
            overview = self.paths.rp_dir / f"{self.paths.rp_dir.name}.md"
            content = self._read_direct(overview)
            if content is None:
                return []
            return [(self._display_key(overview), overview, content, {})]

        if entry_type == "triggered_paths":
            return self._load_triggered_files(triggered_files)

        if entry_type == "triggered_paths_basics":
            return self._load_triggered_files_basics_only(triggered_files)

        self.logger.warning(
            "tiered_loader.unknown_entry",
            context={"entry_type": entry_type},
        )
        return []

    def _load_main_character(self) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
        characters_dir = (self.paths.rp_dir / "characters").resolve()
        if not characters_dir.exists():
            return []
        for char_file in sorted(characters_dir.glob("*.md")):
            if char_file.name == "{{user}}.md":
                continue
            content = self._read_direct(char_file)
            if content is None:
                continue
            meta = self._extract_entity_metadata(char_file, content)
            return [(self._display_key(char_file), char_file, content, meta)]
        return []

    def _load_triggered_files(
        self, triggered_files: Sequence[Path]
    ) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
        collected: list[tuple[str, Path, str, dict[str, Any]]] = []
        seen: set[Path] = set()
        for path in triggered_files:
            target = path.resolve()
            if target in seen:
                continue
            seen.add(target)
            content = self._read_direct(target)
            if content is None:
                continue
            meta = self._extract_entity_metadata(target, content)
            collected.append((self._display_key(target), target, content, meta))
        return collected

    def _load_triggered_files_basics_only(
        self, triggered_files: Sequence[Path]
    ) -> Iterable[tuple[str, Path, str, dict[str, Any]]]:
        """Load triggered files but extract only the 'basics' section.

        This is used for referenced entities to reduce context usage.
        Instead of loading 200-500 lines per entity, we only load ~50 lines
        (name, role, key traits).

        Args:
            triggered_files: Paths to entity files

        Returns:
            Tuples of (display_key, path, basics_content, metadata)
        """
        collected: list[tuple[str, Path, str, dict[str, Any]]] = []
        seen: set[Path] = set()
        for path in triggered_files:
            target = path.resolve()
            if target in seen:
                continue
            seen.add(target)
            full_content = self._read_direct(target)
            if full_content is None:
                continue

            # Extract only the basics section
            basics_content = self._extract_basics_section(target, full_content)

            # Still extract metadata from full content for tracking cores
            meta = self._extract_entity_metadata(target, full_content)

            # Add a marker to indicate this is basics-only
            display_key = f"{self._display_key(target)} (basics)"

            collected.append((display_key, target, basics_content, meta))
        return collected

    def _extract_basics_section(self, path: Path, full_content: str) -> str:
        """Extract only the 'basics' section from an entity file.

        Supports both JSON and Markdown entity formats:
        - JSON: Extract 'basics' field from JSON object
        - Markdown: Extract content between ## Basics and next ## header

        Args:
            path: File path (used to determine format)
            full_content: Full file content

        Returns:
            Basics section content, or full content if basics not found
        """
        # Handle JSON entity files
        if path.suffix == ".json":
            try:
                data = json.loads(full_content)
                basics = data.get("basics", {})
                if isinstance(basics, dict):
                    # Format basics as readable text
                    lines = [f"# {path.stem} (Basics)\n"]
                    for key, value in basics.items():
                        lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
                    return "\n".join(lines)
                elif isinstance(basics, str):
                    return f"# {path.stem} (Basics)\n\n{basics}"
            except json.JSONDecodeError:
                self.logger.warning(
                    "tiered_loader.json_parse_error",
                    context={"path": str(path)},
                )
                return full_content

        # Handle Markdown entity files
        elif path.suffix == ".md":
            lines = full_content.split("\n")
            basics_lines = []
            in_basics = False
            found_basics = False

            for line in lines:
                # Check for ## Basics header (case-insensitive)
                if line.strip().lower().startswith("## basics"):
                    in_basics = True
                    found_basics = True
                    basics_lines.append(line)
                    continue

                # Stop at next ## header
                if in_basics and line.strip().startswith("##"):
                    break

                # Collect lines in basics section
                if in_basics:
                    basics_lines.append(line)

            if found_basics:
                # Add a header indicating this is basics only
                return f"# {path.stem} (Basics)\n\n" + "\n".join(basics_lines)

        # Fallback: return first 50 lines if basics section not found
        self.logger.debug(
            "tiered_loader.basics_not_found",
            context={"path": str(path), "fallback": "first_50_lines"},
        )
        lines = full_content.split("\n")
        truncated = "\n".join(lines[:50])
        return f"# {path.stem} (Summary)\n\n{truncated}\n\n*(Truncated - basics section not found)*"

    def _read_from_base(self, base_key: str, path_value: Path) -> tuple[str | None, dict[str, Any]]:
        if base_key == "config":
            content = self._config_store.read(path_value)
            return content, {}
        content = self._markdown_store.read(path_value)
        meta = self._extract_entity_metadata(
            (self._base_paths[base_key] / path_value).resolve(), content
        )
        return content, meta if meta else {}

    def _extract_entity_metadata(self, path: Path, content: str | None) -> dict[str, Any]:
        if content is None:
            return {}
        parent_name = path.parent.name
        if parent_name not in {"entities", "characters"}:
            return {}
        meta: dict[str, Any] = {"entity_file": str(path)}
        if "Personality Core" in content:
            meta.setdefault("entities_with_cores", []).append(path.stem)
        return meta

    def _read_direct(self, path: Path) -> str | None:
        if not path.exists():
            self.logger.debug(
                "tiered_loader.missing_file",
                context={"path": str(path)},
            )
            return None
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            self.logger.warning(
                "tiered_loader.read_error",
                context={"path": str(path), "error": str(exc)},
            )
            return None

    def _display_key(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.paths.rp_dir))
        except ValueError:
            try:
                return str(path.relative_to(self._base_paths["config"]))
            except ValueError:
                return path.name
