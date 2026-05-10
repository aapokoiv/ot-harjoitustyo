import tkinter as tk
from tkinter import messagebox

from logic.game import ClockConfig, Game
from persistence.analysis_service import StockfishAnalysisService
from persistence.service import MoveStorageService
from ui import theme
from ui.helpers import load_piece_images
from ui.views.game_view import GameView
from ui.views.history_view import HistoryView
from ui.views.menu_view import MenuView
from ui.views.review_view import ReviewView


class ChessApp:
    """Top-level Tk application coordinating views and shared services.

    Attributes:
        root (tk.Tk): Root Tk window.
        service (MoveStorageService): Shared persistence service.
        piece_images (dict[str, tk.PhotoImage]): Loaded chess piece images.
        current_view (tk.Widget | None): Currently displayed view.
        current_view_state (dict | None): Navigation state for the current view.
        view_stack (list[dict]): Back-navigation stack of previous views.
    """

    def __init__(self):
        """Create the application window and show the menu view."""
        self.root = tk.Tk()
        self.root.title(theme.WINDOW_TITLE)
        self.root.geometry(theme.MENU_SIZE)
        self.root.resizable(False, False)
        self.root.configure(bg=theme.COLOR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.service = MoveStorageService()
        self.analysis_service = StockfishAnalysisService(self.service)
        self.piece_images = load_piece_images()
        self.current_view = None
        self.current_view_state = None
        self.view_stack = []

        self.show_menu(add_to_history=False)

    def create_game(self, *, clock_enabled, initial_seconds, increment_seconds):
        """Create a new game and open the game view."""
        game = Game(
            storage_service=self.service,
            clock_config=ClockConfig(
                enabled=clock_enabled,
                initial_seconds=initial_seconds,
                increment_seconds=increment_seconds,
            ),
        )
        self.show_game(game)

    def continue_game(self, game_id):
        """Load an ongoing game and show it to the user."""
        try:
            game = Game.load_existing(game_id, storage_service=self.service)
        except ValueError as error:
            messagebox.showerror("Cannot continue game", str(error), parent=self.root)
            return
        self.show_game(game)

    def open_review(self, game_id):
        """Open the review screen for a saved game."""
        if self.service.get_game(game_id) is None:
            messagebox.showerror("Cannot open review", f"Game {game_id} not found.", parent=self.root)
            return
        self._show_view("review", {"game_id": game_id})

    def open_history(self):
        """Open the history view."""
        self._show_view("history", {})

    def show_menu(self, *, add_to_history=True):
        """Show the main menu view."""
        self._show_view("menu", {}, add_to_history=add_to_history)

    def show_game(self, game, *, add_to_history=True):
        """Show the active game view for ``game``."""
        self._show_view("game", {"game": game}, add_to_history=add_to_history)

    def go_back(self):
        """Navigate back to the previous view if one exists."""
        if not self.view_stack:
            self.show_menu(add_to_history=False)
            return
        target = self.view_stack.pop()
        self._show_view(target["name"], target["state"], add_to_history=False)

    def quit_app(self):
        """Close the application window and backing services."""
        self._close()

    def _show_view(self, view_name, state, *, add_to_history=True):
        if add_to_history and self.current_view_state is not None:
            self.view_stack.append(self.current_view_state)

        if self.current_view is not None:
            on_hide = getattr(self.current_view, "on_hide", None)
            if callable(on_hide):
                on_hide()
            self.current_view.destroy()

        view = self._build_view(view_name, state)
        view.pack(fill="both", expand=True)
        self.current_view = view
        self.current_view_state = {"name": view_name, "state": state}
        self._apply_view_geometry(view_name)
        on_show = getattr(view, "on_show", None)
        if callable(on_show):
            on_show()

    def _build_view(self, view_name, state):
        if view_name == "menu":
            return MenuView(self.root, app=self)
        if view_name == "game":
            return GameView(self.root, app=self, game=state["game"])
        if view_name == "history":
            return HistoryView(self.root, app=self)
        if view_name == "review":
            return ReviewView(self.root, app=self, game_id=state["game_id"])
        raise ValueError(f"Unknown view {view_name}")

    def _apply_view_geometry(self, view_name):
        size_map = {
            "menu": theme.MENU_SIZE,
            "game": theme.GAME_SIZE,
            "history": theme.HISTORY_SIZE,
            "review": theme.REVIEW_SIZE,
        }
        title_map = {
            "menu": theme.WINDOW_TITLE,
            "game": f"{theme.WINDOW_TITLE} - Game",
            "history": f"{theme.WINDOW_TITLE} - History",
            "review": f"{theme.WINDOW_TITLE} - Review",
        }
        self.root.geometry(size_map[view_name])
        self.root.title(title_map[view_name])

    def _close(self):
        if self.current_view is not None:
            on_hide = getattr(self.current_view, "on_hide", None)
            if callable(on_hide):
                on_hide()
        self.service.close()
        self.root.destroy()

    def run(self):
        """Start the Tk event loop."""
        self.root.mainloop()


def run_app():
    """Launch the graphical chess application."""
    ChessApp().run()
