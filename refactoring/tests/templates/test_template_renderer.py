from refactoring.src.infrastructure.templates.state_service import StateTemplateService
from refactoring.src.infrastructure.templates.template_renderer import TemplateRenderer


def test_render_text_substitutes_variables():
    renderer = TemplateRenderer()
    output = renderer.render_text(
        "state/story_arc.md.tpl",
        {"timestamp": "2199-01-01T00:00:00Z", "response_count": 42, "summary": "Arc summary"},
    )
    assert "2199-01-01T00:00:00Z" in output
    assert "Arc summary" in output


def test_render_json_applies_context():
    renderer = TemplateRenderer()
    data = renderer.render_json(
        "entities/character_card.json.tpl",
        {"name": "Aurora", "full_name": "Aurora Lys", "occupation": "Pilot"},
    )
    assert data["name"] == "Aurora"
    assert data["basics"]["occupation"] == "Pilot"


def test_state_template_service_character_card():
    service = StateTemplateService()
    output = service.render_character_card("Aurora Lys")
    assert "Aurora Lys" in output


def test_state_template_service_preferences():
    service = StateTemplateService()
    data = service.render_character_preferences("Aurora Lys")
    assert data["character_name"] == "Aurora Lys"
    assert "likes" in data["preferences"]
