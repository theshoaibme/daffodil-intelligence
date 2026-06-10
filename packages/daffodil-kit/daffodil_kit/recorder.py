"""
Action Recorder Module
=======================
Records all mouse and keyboard actions performed by the user,
storing them as a timestamped action list for later replay.

Uses pynput listeners which run in background threads.
"""

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not installed. Action recording disabled. Run: pip install pynput")


@dataclass
class Action:
    """A single recorded user action."""
    type: str                           # 'mouse_move', 'mouse_click', 'mouse_scroll', 'key_press', 'key_type'
    timestamp: float                    # Epoch time
    x: Optional[int] = None            # Screen X (for mouse actions)
    y: Optional[int] = None            # Screen Y (for mouse actions)
    button: Optional[str] = None       # Mouse button ('left', 'right', 'middle')
    pressed: Optional[bool] = None     # True = pressed, False = released
    dy: Optional[int] = None           # Scroll delta
    key: Optional[str] = None          # Key name
    text: Optional[str] = None         # Typed character
    delay_after: float = 0.0           # Computed delay before next action


@dataclass
class Recording:
    """A complete recorded session."""
    name: str
    created_at: float = field(default_factory=time.time)
    duration: float = 0.0
    action_count: int = 0
    actions: List[Action] = field(default_factory=list)


class ActionRecorder:
    """
    Records mouse and keyboard actions in real-time.

    Usage:
        recorder = ActionRecorder()
        recorder.start("my_macro")
        # ... user performs actions ...
        recording = recorder.stop()
        recorder.save(recording)
    """

    RECORDINGS_DIR = Path("recordings")
    DB_PATH = Path("recordings/copycat.db")

    def __init__(self):
        self._recording: Optional[Recording] = None
        self._mouse_listener = None
        self._keyboard_listener = None
        self._lock = threading.Lock()
        self._start_time: float = 0
        self._last_action_time: float = 0
        self.RECORDINGS_DIR.mkdir(exist_ok=True)
        self._init_db()
        self._migrate_json_files()

    def _init_db(self):
        import sqlite3
        with self._lock:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    name TEXT PRIMARY KEY,
                    created_at REAL,
                    duration REAL,
                    action_count INTEGER,
                    actions TEXT
                )
            """)
            conn.commit()
            conn.close()

    def _migrate_json_files(self):
        """Migrate any existing legacy JSON recordings into SQLite database."""
        import sqlite3
        for path in self.RECORDINGS_DIR.glob("*.json"):
            if path.name == "copycat.db":
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                name = data.get("name", path.stem)
                created_at = data.get("created_at", 0.0)
                duration = data.get("duration", 0.0)
                action_count = data.get("action_count", 0)
                actions_str = json.dumps(data.get("actions", []))

                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO recordings (name, created_at, duration, action_count, actions) VALUES (?, ?, ?, ?, ?)",
                    (name, created_at, duration, action_count, actions_str)
                )
                conn.commit()
                conn.close()
                
                # Delete migrated JSON file
                path.unlink()
                logger.info(f"Successfully migrated legacy JSON recording '{name}' into SQLite.")
            except Exception as e:
                logger.error(f"Failed to migrate legacy JSON recording {path}: {e}")

    @property
    def is_recording(self) -> bool:
        return self._recording is not None

    def start(self, name: str = None) -> bool:
        """
        Start recording user actions.
        Returns False if already recording.
        """
        if not PYNPUT_AVAILABLE:
            logger.error("pynput not available — cannot record")
            return False

        if self.is_recording:
            logger.warning("Already recording — stop current recording first")
            return False

        if name is None:
            name = f"recording_{int(time.time())}"

        self._recording = Recording(name=name)
        self._start_time = time.time()
        self._last_action_time = self._start_time

        # Start mouse listener
        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._mouse_listener.start()

        # Start keyboard listener
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

        logger.info(f"Recording started: {name}")
        return True

    def stop(self) -> Optional[Recording]:
        """
        Stop recording and return the completed Recording object.
        Returns None if not recording.
        """
        if not self.is_recording:
            return None

        # Stop listeners
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        with self._lock:
            recording = self._recording
            self._recording = None

        if recording:
            recording.duration = time.time() - self._start_time
            recording.action_count = len(recording.actions)
            # Compute delays between actions
            for i in range(1, len(recording.actions)):
                recording.actions[i - 1].delay_after = (
                    recording.actions[i].timestamp - recording.actions[i - 1].timestamp
                )

        logger.info(f"Recording stopped: {recording.name}, {recording.action_count} actions, {recording.duration:.1f}s")
        return recording

    def save(self, recording: Recording, path: Optional[Path] = None) -> Path:
        """Save a recording to the SQLite database."""
        import sqlite3
        actions_str = json.dumps([asdict(a) for a in recording.actions])
        
        with self._lock:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO recordings (name, created_at, duration, action_count, actions) VALUES (?, ?, ?, ?, ?)",
                (recording.name, recording.created_at, recording.duration, recording.action_count, actions_str)
            )
            conn.commit()
            conn.close()

        logger.info(f"Recording '{recording.name}' saved to SQLite database")
        return self.DB_PATH

    def load(self, name: str) -> Optional[Recording]:
        """Load a recording from SQLite database by name."""
        import sqlite3
        with self._lock:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, created_at, duration, action_count, actions FROM recordings WHERE name = ?", (name,))
            row = cursor.fetchone()
            conn.close()

        if not row:
            logger.error(f"Recording not found in SQLite: {name}")
            return None

        actions_list = json.loads(row[4])
        actions = [Action(**a) for a in actions_list]
        recording = Recording(
            name=row[0],
            created_at=row[1],
            duration=row[2],
            action_count=row[3],
            actions=actions,
        )
        return recording

    def list_recordings(self) -> List[Dict]:
        """List all saved recordings with metadata from SQLite database."""
        import sqlite3
        recordings = []
        with self._lock:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, created_at, duration, action_count FROM recordings ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()

        for row in rows:
            recordings.append({
                "name": row[0],
                "created_at": row[1],
                "duration": row[2],
                "action_count": row[3],
                "file": str(self.DB_PATH),
            })
        return recordings

    def delete(self, name: str) -> bool:
        """Delete a saved recording by name from SQLite database."""
        import sqlite3
        with self._lock:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recordings WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
        return deleted

    # ─── Event handlers (run in pynput background threads) ──────────────────

    def _add_action(self, action: Action):
        with self._lock:
            if self._recording:
                self._recording.actions.append(action)

    def _on_mouse_move(self, x: int, y: int):
        # Skip recording every single move event — only record occasionally
        # to avoid flooding. Record one every ~10 pixels of movement.
        if len(self._recording.actions) == 0:
            self._add_action(Action(type="mouse_move", timestamp=time.time(), x=x, y=y))
            return
        last = self._recording.actions[-1]
        if last.type == "mouse_move":
            dx = abs(x - (last.x or 0))
            dy = abs(y - (last.y or 0))
            if dx < 10 and dy < 10:
                return  # Skip tiny movements
        self._add_action(Action(type="mouse_move", timestamp=time.time(), x=x, y=y))

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        btn_name = button.name if hasattr(button, 'name') else str(button)
        self._add_action(Action(
            type="mouse_click",
            timestamp=time.time(),
            x=x, y=y,
            button=btn_name,
            pressed=pressed,
        ))

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        self._add_action(Action(
            type="mouse_scroll",
            timestamp=time.time(),
            x=x, y=y,
            dy=dy,
        ))

    def _on_key_press(self, key):
        try:
            char = key.char
            self._add_action(Action(type="key_type", timestamp=time.time(), text=char))
        except AttributeError:
            key_name = key.name if hasattr(key, 'name') else str(key)
            self._add_action(Action(type="key_press", timestamp=time.time(), key=key_name, pressed=True))

    def _on_key_release(self, key):
        try:
            key.char  # Regular char — don't record release
        except AttributeError:
            key_name = key.name if hasattr(key, 'name') else str(key)
            self._add_action(Action(type="key_press", timestamp=time.time(), key=key_name, pressed=False))


# Global recorder singleton
_recorder = ActionRecorder()


def get_recorder() -> ActionRecorder:
    return _recorder
