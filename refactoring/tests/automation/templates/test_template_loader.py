"""Unit tests for TemplateLoader.

Tests template loading with caching:
- Template loading from JSON files
- Template validation
- Caching behavior
- Section extraction
- Error handling
"""

import json
import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.templates.template_cache import TemplateCache
from refactoring.src.automation.templates.template_loader import TemplateLoader


@pytest.fixture
def temp_template_dir():
    """Create temporary template directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "templates"
        template_dir.mkdir()
        yield template_dir


@pytest.fixture
def valid_template_data():
    """Create valid template data."""
    return {
        "display_name": "Fantasy",
        "description": "Fantasy genre template",
        "sections": {
            "tone_and_atmosphere": {
                "title": "Tone & Atmosphere",
                "content": ["Create magical atmosphere", "Use descriptive language"],
            },
            "pacing": {
                "title": "Pacing",
                "content": ["Balance action and reflection"],
            },
        },
        "highlights": ["Magic", "Adventure"],
    }


class TestBasicLoading:
    """Test basic template loading."""

    def test_load_template_by_name(self, temp_template_dir, valid_template_data):
        """Test loading template by name."""
        # Create template file
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("fantasy")

        assert template is not None
        assert template["display_name"] == "Fantasy"

    def test_load_template_with_json_extension(self, temp_template_dir, valid_template_data):
        """Test loading template with .json extension."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("fantasy.json")

        assert template is not None
        assert template["display_name"] == "Fantasy"

    def test_load_nonexistent_template_returns_none(self, temp_template_dir):
        """Test loading nonexistent template returns None."""
        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("notfound")

        assert template is None

    def test_load_template_preserves_all_fields(self, temp_template_dir, valid_template_data):
        """Test all template fields are preserved."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("fantasy")

        assert template["display_name"] == valid_template_data["display_name"]
        assert template["description"] == valid_template_data["description"]
        assert template["sections"] == valid_template_data["sections"]
        assert template["highlights"] == valid_template_data["highlights"]


class TestTemplateValidation:
    """Test template validation."""

    def test_valid_template_loads(self, temp_template_dir, valid_template_data):
        """Test valid template passes validation."""
        template_file = temp_template_dir / "valid.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("valid")

        assert template is not None

    def test_missing_display_name_rejected(self, temp_template_dir):
        """Test template without display_name is rejected."""
        invalid_data = {
            "sections": {
                "tone": {"title": "Tone", "content": ["Item"]},
            }
        }

        template_file = temp_template_dir / "invalid.json"
        template_file.write_text(json.dumps(invalid_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None

    def test_missing_sections_rejected(self, temp_template_dir):
        """Test template without sections is rejected."""
        invalid_data = {"display_name": "Test"}

        template_file = temp_template_dir / "invalid.json"
        template_file.write_text(json.dumps(invalid_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None

    def test_section_missing_title_rejected(self, temp_template_dir):
        """Test section without title is rejected."""
        invalid_data = {
            "display_name": "Test",
            "sections": {
                "tone": {"content": ["Item"]},  # Missing title
            },
        }

        template_file = temp_template_dir / "invalid.json"
        template_file.write_text(json.dumps(invalid_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None

    def test_section_missing_content_rejected(self, temp_template_dir):
        """Test section without content is rejected."""
        invalid_data = {
            "display_name": "Test",
            "sections": {
                "tone": {"title": "Tone"},  # Missing content
            },
        }

        template_file = temp_template_dir / "invalid.json"
        template_file.write_text(json.dumps(invalid_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None

    def test_content_not_list_rejected(self, temp_template_dir):
        """Test section with non-list content is rejected."""
        invalid_data = {
            "display_name": "Test",
            "sections": {
                "tone": {"title": "Tone", "content": "Not a list"},
            },
        }

        template_file = temp_template_dir / "invalid.json"
        template_file.write_text(json.dumps(invalid_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None


class TestCaching:
    """Test template caching behavior."""

    def test_template_cached_after_load(self, temp_template_dir, valid_template_data):
        """Test template is cached after first load."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        cache = TemplateCache(max_size=10)
        loader = TemplateLoader(temp_template_dir, cache=cache)

        # First load
        template1 = loader.load_template("fantasy")

        # Second load (should be from cache)
        template2 = loader.load_template("fantasy")

        # Should be same object (cached)
        assert template1 is template2

    def test_cache_stats_updated(self, temp_template_dir, valid_template_data):
        """Test cache stats are updated correctly."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        cache = TemplateCache(max_size=10)
        loader = TemplateLoader(temp_template_dir, cache=cache)

        # Load template
        loader.load_template("fantasy")

        stats = loader.get_cache_stats()
        assert stats["size"] == 1

        # Load again (cache hit)
        loader.load_template("fantasy")

        stats = loader.get_cache_stats()
        assert stats["hits"] == 1

    def test_invalidate_cache(self, temp_template_dir, valid_template_data):
        """Test cache invalidation forces reload."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        cache = TemplateCache(max_size=10)
        loader = TemplateLoader(temp_template_dir, cache=cache)

        # Load and cache
        template1 = loader.load_template("fantasy")

        # Invalidate
        was_cached = loader.invalidate_cache("fantasy")
        assert was_cached is True

        # Load again (not from cache)
        template2 = loader.load_template("fantasy")

        # Should be different objects
        assert template1 is not template2
        # But same content
        assert template1["display_name"] == template2["display_name"]

    def test_invalidate_nonexistent_returns_false(self, temp_template_dir):
        """Test invalidating nonexistent template returns False."""
        loader = TemplateLoader(temp_template_dir)

        was_cached = loader.invalidate_cache("notfound")
        assert was_cached is False


class TestSectionExtraction:
    """Test loading specific sections."""

    def test_load_specific_sections(self, temp_template_dir, valid_template_data):
        """Test loading only specified sections."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        sections = loader.load_template_sections("fantasy", ["tone_and_atmosphere"])

        assert len(sections) == 1
        assert "tone_and_atmosphere" in sections
        assert "pacing" not in sections

    def test_load_multiple_sections(self, temp_template_dir, valid_template_data):
        """Test loading multiple specified sections."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        sections = loader.load_template_sections("fantasy", ["tone_and_atmosphere", "pacing"])

        assert len(sections) == 2
        assert "tone_and_atmosphere" in sections
        assert "pacing" in sections

    def test_load_nonexistent_section_skipped(self, temp_template_dir, valid_template_data):
        """Test nonexistent sections are skipped."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)
        sections = loader.load_template_sections("fantasy", ["tone_and_atmosphere", "nonexistent"])

        assert len(sections) == 1
        assert "tone_and_atmosphere" in sections
        assert "nonexistent" not in sections

    def test_load_sections_from_nonexistent_template(self, temp_template_dir):
        """Test loading sections from nonexistent template returns empty."""
        loader = TemplateLoader(temp_template_dir)
        sections = loader.load_template_sections("notfound", ["tone"])

        assert sections == {}


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json_handled(self, temp_template_dir):
        """Test invalid JSON is handled gracefully."""
        template_file = temp_template_dir / "invalid.json"
        template_file.write_text("{ invalid json }", encoding="utf-8")

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("invalid")

        assert template is None

    def test_non_dict_json_rejected(self, temp_template_dir):
        """Test JSON that's not a dict is rejected."""
        template_file = temp_template_dir / "array.json"
        template_file.write_text('["not", "a", "dict"]', encoding="utf-8")

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("array")

        assert template is None

    def test_empty_json_object_rejected(self, temp_template_dir):
        """Test empty JSON object fails validation."""
        template_file = temp_template_dir / "empty.json"
        template_file.write_text("{}", encoding="utf-8")

        loader = TemplateLoader(temp_template_dir)
        template = loader.load_template("empty")

        assert template is None


class TestCustomCache:
    """Test using custom cache instance."""

    def test_shared_cache_across_loaders(self, temp_template_dir, valid_template_data):
        """Test multiple loaders can share a cache."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        # Create shared cache
        shared_cache = TemplateCache(max_size=10)

        # Create two loaders with same cache
        loader1 = TemplateLoader(temp_template_dir, cache=shared_cache)
        loader2 = TemplateLoader(temp_template_dir, cache=shared_cache)

        # Load with first loader
        template1 = loader1.load_template("fantasy")

        # Load with second loader (should use cached version)
        template2 = loader2.load_template("fantasy")

        # Should be same cached object
        assert template1 is template2

    def test_default_cache_created(self, temp_template_dir, valid_template_data):
        """Test default cache is created if none provided."""
        template_file = temp_template_dir / "fantasy.json"
        template_file.write_text(json.dumps(valid_template_data, indent=2))

        loader = TemplateLoader(temp_template_dir)  # No cache provided

        template = loader.load_template("fantasy")

        assert template is not None
        # Cache should exist
        stats = loader.get_cache_stats()
        assert stats["size"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
