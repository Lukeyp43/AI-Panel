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

            # Check if this is a valid key press (not just a modifier being held)
            is_valid_key = key in key_map or (event.text() and event.text().isprintable())

            # Maximum of 3 keys allowed - show error if trying to add more
            if len(self.pressed_keys) >= 3 and is_valid_key:
                tooltip("Maximum of 3 keys allowed for shortcuts")
                return

            # Add key to list if not already present (preserves order)
            if key in key_map:
                key_name = key_map[key]
                if key_name not in self.pressed_keys:
                    self.pressed_keys.append(key_name)
            elif event.text() and event.text().isprintable():
                key_name = event.text().upper()
                if key_name not in self.pressed_keys:
                    self.pressed_keys.append(key_name)

            # Update display if method exists
            if hasattr(self, '_update_recording_display'):
                self._update_recording_display(self.pressed_keys)

            # Auto-stop after 500ms, or immediately if we hit 3 keys
            if len(self.pressed_keys) > 0:
                if len(self.pressed_keys) >= 3:
                    # Stop immediately when we reach 3 keys
                    QTimer.singleShot(100, self.stop_recording)
                else:
                    # Otherwise wait 500ms for more keys
                    QTimer.singleShot(500, self.stop_recording)
        else:
            # Pass event to parent if not recording
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release - only pass to parent if not recording"""
        if not self.recording_keys:
            super().keyReleaseEvent(event)
