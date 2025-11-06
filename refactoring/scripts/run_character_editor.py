from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from character_manager import CharacterManager


class CharacterApp(App):
    """A Textual app for managing characters."""

    CSS = """
    Screen {
        background: $surface;
    }

    CharacterManager {
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield CharacterManager()
        yield Footer()


if __name__ == "__main__":
    app = CharacterApp()
    app.run()
