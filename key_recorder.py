"""
Shared key recording logic for keyboard shortcuts.
Used by both Templates and Quick Actions settings.
"""

import sys

try:
    from PyQt6.QtCore import Qt, QTimer
except ImportError:
    from PyQt5.QtCore import Qt, QTimer

from aqt.utils import tooltip


class KeyRecorderMixin:
    """Mixin class that provides key recording functionality for QWidget subclasses"""

    def setup_key_recorder(self):
        """Initialize key recorder state. Call this in __init__"""
        self.recording_keys = False
        self.pressed_keys = []
        self.recording_timer = None  # Timer to auto-stop recording

    def start_recording(self):
        """Start recording keyboard shortcuts"""
        self.recording_keys = True
        self.pressed_keys = []
        self.grabKeyboard()

    def stop_recording(self):
        """Stop recording keyboard shortcuts"""
        if not self.recording_keys:
            return

        self.recording_keys = False
        self.releaseKeyboard()

        # Cancel any pending timer
        if self.recording_timer is not None:
            self.recording_timer.stop()
            self.recording_timer = None

        # Save the recorded keys
        if hasattr(self, '_on_keys_recorded') and self.pressed_keys:
            self._on_keys_recorded(self.pressed_keys.copy())

    def keyPressEvent(self, event):
        """Capture key presses when recording (max 3 keys)"""
        if self.recording_keys:
            key = event.key()

            # On macOS, Qt has a quirk where Control and Meta are swapped:
            # - Qt.Key_Control is actually triggered by the Cmd key (⌘)
            # - Qt.Key_Meta is actually triggered by the Control key (⌃)
            # So we need to swap them in our mapping to match user expectations
            if sys.platform == "darwin":
                key_map = {
                    Qt.Key.Key_Control if hasattr(Qt.Key, 'Key_Control') else Qt.Key_Control: "Meta",  # Cmd key
                    Qt.Key.Key_Meta if hasattr(Qt.Key, 'Key_Meta') else Qt.Key_Meta: "Control",  # Control key
                    Qt.Key.Key_Shift if hasattr(Qt.Key, 'Key_Shift') else Qt.Key_Shift: "Shift",
                    Qt.Key.Key_Alt if hasattr(Qt.Key, 'Key_Alt') else Qt.Key_Alt: "Alt",
                }
            else:
                key_map = {
                    Qt.Key.Key_Control if hasattr(Qt.Key, 'Key_Control') else Qt.Key_Control: "Control/Meta",
                    Qt.Key.Key_Meta if hasattr(Qt.Key, 'Key_Meta') else Qt.Key_Meta: "Control/Meta",
                    Qt.Key.Key_Shift if hasattr(Qt.Key, 'Key_Shift') else Qt.Key_Shift: "Shift",
                    Qt.Key.Key_Alt if hasattr(Qt.Key, 'Key_Alt') else Qt.Key_Alt: "Alt",
                }

            # Determine the key name
            key_name = None

            # Check if it's a modifier key
            if key in key_map:
                key_name = key_map[key]
            # Check if it's a letter key (A-Z)
            elif key >= (Qt.Key.Key_A if hasattr(Qt.Key, 'Key_A') else Qt.Key_A) and \
                 key <= (Qt.Key.Key_Z if hasattr(Qt.Key, 'Key_Z') else Qt.Key_Z):
                # Convert Qt key code to letter (Qt.Key_A = 65 = 'A')
                key_name = chr(key).upper()
            # Check if it's a number key (0-9)
            elif key >= (Qt.Key.Key_0 if hasattr(Qt.Key, 'Key_0') else Qt.Key_0) and \
                 key <= (Qt.Key.Key_9 if hasattr(Qt.Key, 'Key_9') else Qt.Key_9):
                key_name = chr(key)
            # Fall back to event.text() for other printable characters
            elif event.text() and event.text().isprintable():
                key_name = event.text().upper()

            # Maximum of 3 keys allowed - show error if trying to add more
            if key_name and len(self.pressed_keys) >= 3:
                tooltip("Maximum of 3 keys allowed for shortcuts")
                return

            # Add key to list if not already present (preserves order)
            if key_name and key_name not in self.pressed_keys:
                self.pressed_keys.append(key_name)

            # Update display if method exists
            if hasattr(self, '_update_recording_display'):
                self._update_recording_display(self.pressed_keys)

            # Cancel any existing timer before creating a new one
            if self.recording_timer is not None:
                self.recording_timer.stop()
                self.recording_timer = None

            # Auto-stop after 500ms, or immediately if we hit 3 keys
            if len(self.pressed_keys) > 0:
                self.recording_timer = QTimer(self)
                self.recording_timer.setSingleShot(True)
                self.recording_timer.timeout.connect(self.stop_recording)

                if len(self.pressed_keys) >= 3:
                    # Stop immediately when we reach 3 keys
                    self.recording_timer.start(100)
                else:
                    # Otherwise wait 500ms for more keys
                    self.recording_timer.start(500)
        else:
            # Pass event to parent if not recording
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release - only pass to parent if not recording"""
        if not self.recording_keys:
            super().keyReleaseEvent(event)
