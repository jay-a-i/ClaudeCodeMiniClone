import sys
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input
from textual.reactive import reactive

class Agent_J(App):
    """An app featuring a transition from a splash screen to a live chat interface."""
    
    # 1. Properly link the CSS file path
    CSS_PATH = "tui.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    # Reactive state determines if we show the banner or the chat
    chat_started = reactive(False)

    def compose(self) -> ComposeResult:
        # We wrap everything inside a main container to easily swap views
        yield Vertical(id="main-container")

    def on_mount(self) -> None:
        """Runs when the app starts; shows the initial splash screen banner."""
        self.show_splash_screen()

    def show_splash_screen(self) -> None:
        container = self.query_one("#main-container")
        container.mount(
            Vertical(
                Static(
                    " █████   ██████  ███████ ███    ██ ████████            ██ \n"
                    "██   ██ ██       ██      ████   ██    ██               ██ \n"
                    "███████ ██   ███ █████   ██ ██  ██    ██    ████       ██ \n"
                    "██   ██ ██    ██ ██      ██  ██ ██    ██          ██   ██ \n"
                    "██   ██  ██████  ███████ ██   ████    ██           █████  ",
                    id="agent-title"
                ),
                Static("Your Personal Secure AI Coding Assistant!", id="tagline"),
                id="console-box"
            ),
            Static("Press 'Enter' to begin...", id='prompt-line')
        )
        # Give focus to the screen so it catches keypresses
        self.screen.focus()

    def on_key(self, event) -> None:
        """Listens for the Enter key to transition to the chat layout."""
        if event.key == "enter" and not self.chat_started:
            self.chat_started = True
            self.start_chat_interface()

    def start_chat_interface(self) -> None:
        """Clears the splash screen banner and draws the chat history + input fields."""
        container = self.query_one("#main-container")
        container.remove_children()  # Clear splash screen widgets
        
        # Build out the chat structure
        history = VerticalScroll(id='chat_history')
        chat_input = Input(placeholder="Ask a question or type a command...", id="chat_prompt")
        
        container.mount(history)
        container.mount(chat_input)
        
        # Add the first message and focus input box
        history.mount(Static("🤖 AGENT-J: Ready for commands. Type below.", classes="agent-msg"))
        chat_input.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handles what happens when you type something and press Enter in the chat box."""
        user_text = event.value.strip()
        if not user_text:
            return

        # Clear input box
        input_widget = self.query_one("#chat_prompt", Input)
        input_widget.value = ""

        # Append user message
        history = self.query_one("#chat_history")
        history.mount(Static(f"👤 YOU: {user_text}", classes="user-msg"))
        
        # Simple Echo response dummy logic (Replace with your actual AI/subprocess agent calls)
        history.mount(Static(f"🤖 AGENT-J: I received your request: '{user_text}'", classes="agent-msg"))
        history.scroll_end(animate=False)

if __name__ == "__main__":
    app = Agent_J()
    app.run()