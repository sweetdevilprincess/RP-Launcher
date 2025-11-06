"""Unit tests for PatternLoader.

Tests pattern loading and parsing from entity files:
- File discovery (characters/, entities/)
- Pattern extraction (keywords, regex, semantic)
- Multiple trigger formats
- Entity name extraction
- Caching behavior
- Error handling
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.pattern_loader import PatternLoader


@pytest.fixture
def temp_rp_dir():
    """Create temporary RP directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir) / "test_rp"
        rp_dir.mkdir()
        (rp_dir / "characters").mkdir()
        (rp_dir / "entities").mkdir()
        yield rp_dir


class TestFileDiscovery:
    """Test pattern file discovery."""

    def test_discover_characters_directory(self, temp_rp_dir):
        """Test discovery of files in characters/ directory."""
        loader = PatternLoader()

        # Create character file with triggers
        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice, allie", encoding="utf-8")

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        assert len(patterns_list) == 1
        assert patterns_list[0].entity_name == "Alice"

    def test_discover_entities_directory(self, temp_rp_dir):
        """Test discovery of files in entities/ directory."""
        loader = PatternLoader()

        # Create entity file with triggers
        entity_file = temp_rp_dir / "entities" / "Sword.md"
        entity_file.write_text("**Triggers**: sword, blade", encoding="utf-8")

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        assert len(patterns_list) == 1
        assert patterns_list[0].entity_name == "Sword"

    def test_discover_both_directories(self, temp_rp_dir):
        """Test discovery from both characters/ and entities/."""
        loader = PatternLoader()

        # Create files in both directories
        (temp_rp_dir / "characters" / "Alice.md").write_text(
            "**Triggers**: alice", encoding="utf-8"
        )
        (temp_rp_dir / "entities" / "Sword.md").write_text("**Triggers**: sword", encoding="utf-8")

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        assert len(patterns_list) == 2
        entity_names = {p.entity_name for p in patterns_list}
        assert entity_names == {"Alice", "Sword"}

    def test_missing_directories_no_error(self, temp_rp_dir):
        """Test graceful handling when directories don't exist."""
        loader = PatternLoader()

        # Remove directories
        import shutil

        shutil.rmtree(temp_rp_dir / "characters")
        shutil.rmtree(temp_rp_dir / "entities")

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        assert len(patterns_list) == 0

    def test_ignore_files_without_triggers(self, temp_rp_dir):
        """Test files without triggers are filtered out."""
        loader = PatternLoader()

        # Create file without triggers
        (temp_rp_dir / "characters" / "NoTriggers.md").write_text(
            "Just some content", encoding="utf-8"
        )

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        assert len(patterns_list) == 0


class TestKeywordParsing:
    """Test keyword trigger parsing."""

    def test_parse_markdown_format(self, temp_rp_dir):
        """Test **Triggers**: format parsing."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice, allie, ally", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns is not None
        assert patterns.keywords == ["alice", "allie", "ally"]

    def test_parse_bracket_format(self, temp_rp_dir):
        """Test [Triggers:...] format parsing."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Bob.md"
        char_file.write_text("[Triggers:bob,bobby]", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns is not None
        assert patterns.keywords == ["bob", "bobby"]

    def test_parse_strips_whitespace(self, temp_rp_dir):
        """Test keyword whitespace is trimmed."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**:  alice  ,  allie  ,  ally  ", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == ["alice", "allie", "ally"]

    def test_parse_case_insensitive_header(self, temp_rp_dir):
        """Test **triggers**: vs **Triggers**: is case-insensitive."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == ["alice"]

    def test_parse_multiple_trigger_lines_last_wins(self, temp_rp_dir):
        """Test when multiple trigger lines exist, last one is used."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: old\n**Triggers**: alice, allie", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        # Last definition wins
        assert patterns.keywords == ["alice", "allie"]

    def test_parse_empty_triggers(self, temp_rp_dir):
        """Test empty trigger list."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**:", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == []


class TestRegexParsing:
    """Test regex trigger parsing."""

    def test_parse_regex_triggers(self, temp_rp_dir):
        """Test [RegexTriggers:...] format parsing."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("[RegexTriggers:ali[cs]e,\\bAlice\\b]", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.regex_patterns == [r"ali[cs]e", r"\bAlice\b"]

    def test_parse_regex_strips_whitespace(self, temp_rp_dir):
        """Test regex whitespace is trimmed."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("[RegexTriggers: alice , allie ]", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.regex_patterns == ["alice", "allie"]


class TestSemanticParsing:
    """Test semantic trigger parsing."""

    def test_parse_semantic_triggers(self, temp_rp_dir):
        """Test [SemanticTriggers:...] format parsing."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text(
            "[SemanticTriggers:References to Alice,Alice's family]",
            encoding="utf-8",
        )

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.semantic_descriptions == [
            "References to Alice",
            "Alice's family",
        ]

    def test_parse_semantic_strips_whitespace(self, temp_rp_dir):
        """Test semantic description whitespace is trimmed."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text(
            "[SemanticTriggers: Alice mentioned ,  Her friends ]",
            encoding="utf-8",
        )

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.semantic_descriptions == ["Alice mentioned", "Her friends"]


class TestMixedParsing:
    """Test parsing multiple trigger types together."""

    def test_parse_all_three_types(self, temp_rp_dir):
        """Test parsing keywords, regex, and semantic together."""
        loader = PatternLoader()

        content = """# Alice

**Triggers**: alice, allie
[RegexTriggers:ali[cs]e]
[SemanticTriggers:References to Alice]
"""

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text(content, encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == ["alice", "allie"]
        assert patterns.regex_patterns == [r"ali[cs]e"]
        assert patterns.semantic_descriptions == ["References to Alice"]

    def test_parse_only_keywords(self, temp_rp_dir):
        """Test file with only keywords."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == ["alice"]
        assert patterns.regex_patterns == []
        assert patterns.semantic_descriptions == []

    def test_parse_only_regex(self, temp_rp_dir):
        """Test file with only regex."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("[RegexTriggers:alice]", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.keywords == []
        assert patterns.regex_patterns == ["alice"]
        assert patterns.semantic_descriptions == []


class TestEntityNameExtraction:
    """Test entity name extraction from filenames."""

    def test_extract_simple_name(self, temp_rp_dir):
        """Test extracting name from simple filename."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.entity_name == "Alice"

    def test_extract_name_with_char_prefix(self, temp_rp_dir):
        """Test extracting name with [CHAR] prefix."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "[CHAR] Alice Smith.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.entity_name == "Alice Smith"

    def test_extract_name_with_loc_prefix(self, temp_rp_dir):
        """Test extracting name with [LOC] prefix."""
        loader = PatternLoader()

        entity_file = temp_rp_dir / "entities" / "[LOC] City Square.md"
        entity_file.write_text("**Triggers**: square", encoding="utf-8")

        patterns = loader.load_patterns_from_file(entity_file)

        assert patterns.entity_name == "City Square"

    def test_extract_name_with_item_prefix(self, temp_rp_dir):
        """Test extracting name with [ITEM] prefix."""
        loader = PatternLoader()

        entity_file = temp_rp_dir / "entities" / "[ITEM] Magic Sword.md"
        entity_file.write_text("**Triggers**: sword", encoding="utf-8")

        patterns = loader.load_patterns_from_file(entity_file)

        assert patterns.entity_name == "Magic Sword"

    def test_extract_name_preserves_spaces(self, temp_rp_dir):
        """Test name extraction preserves spaces."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice Marie Smith.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.entity_name == "Alice Marie Smith"


class TestCaching:
    """Test pattern caching behavior."""

    def test_cache_stores_patterns(self, temp_rp_dir):
        """Test patterns are cached after first load."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        # First load
        patterns1 = loader.load_patterns_from_file(char_file)

        # Second load (from cache)
        patterns2 = loader.load_patterns_from_file(char_file)

        # Should be same object (cached)
        assert patterns1 is patterns2

    def test_cache_returns_same_patterns(self, temp_rp_dir):
        """Test cached patterns have same content."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice, allie", encoding="utf-8")

        patterns1 = loader.load_patterns_from_file(char_file)
        patterns2 = loader.load_patterns_from_file(char_file)

        assert patterns1.keywords == patterns2.keywords
        assert patterns1.entity_name == patterns2.entity_name

    def test_clear_cache(self, temp_rp_dir):
        """Test cache can be cleared."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        # Load and cache
        patterns1 = loader.load_patterns_from_file(char_file)

        # Clear cache
        loader.clear_cache()

        # Load again (not from cache)
        patterns2 = loader.load_patterns_from_file(char_file)

        # Should be different objects
        assert patterns1 is not patterns2
        # But same content
        assert patterns1.keywords == patterns2.keywords

    def test_cache_independent_per_file(self, temp_rp_dir):
        """Test cache is independent for different files."""
        loader = PatternLoader()

        alice_file = temp_rp_dir / "characters" / "Alice.md"
        alice_file.write_text("**Triggers**: alice", encoding="utf-8")

        bob_file = temp_rp_dir / "characters" / "Bob.md"
        bob_file.write_text("**Triggers**: bob", encoding="utf-8")

        alice_patterns = loader.load_patterns_from_file(alice_file)
        bob_patterns = loader.load_patterns_from_file(bob_file)

        assert alice_patterns.entity_name == "Alice"
        assert bob_patterns.entity_name == "Bob"


class TestErrorHandling:
    """Test error handling for invalid files."""

    def test_unreadable_file_returns_none(self, temp_rp_dir):
        """Test unreadable file returns None."""
        loader = PatternLoader()

        # Non-existent file
        char_file = temp_rp_dir / "characters" / "NotFound.md"

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns is None

    def test_invalid_encoding_handled(self, temp_rp_dir):
        """Test file with invalid encoding is handled gracefully."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Invalid.md"
        # Write binary data that's not valid UTF-8
        char_file.write_bytes(b"\xff\xfe Invalid UTF-8")

        patterns = loader.load_patterns_from_file(char_file)

        # Should handle gracefully (return None or use error recovery)
        # Exact behavior depends on implementation
        assert patterns is None or patterns.keywords == []

    def test_empty_file_returns_empty_patterns(self, temp_rp_dir):
        """Test empty file returns patterns with no triggers."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Empty.md"
        char_file.write_text("", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns is not None
        assert patterns.keywords == []
        assert patterns.regex_patterns == []
        assert patterns.semantic_descriptions == []


class TestFilePathPreservation:
    """Test that file paths are preserved correctly."""

    def test_file_path_stored(self, temp_rp_dir):
        """Test file path is stored in patterns."""
        loader = PatternLoader()

        char_file = temp_rp_dir / "characters" / "Alice.md"
        char_file.write_text("**Triggers**: alice", encoding="utf-8")

        patterns = loader.load_patterns_from_file(char_file)

        assert patterns.file_path == char_file

    def test_file_paths_unique_per_file(self, temp_rp_dir):
        """Test each file gets its own path."""
        loader = PatternLoader()

        alice_file = temp_rp_dir / "characters" / "Alice.md"
        alice_file.write_text("**Triggers**: alice", encoding="utf-8")

        bob_file = temp_rp_dir / "characters" / "Bob.md"
        bob_file.write_text("**Triggers**: bob", encoding="utf-8")

        patterns_list = loader.load_all_patterns(temp_rp_dir)

        paths = [p.file_path for p in patterns_list]
        assert len(set(paths)) == 2  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
