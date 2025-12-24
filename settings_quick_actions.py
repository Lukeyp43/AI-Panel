"""
Settings Quick Actions View - Configure keyboard shortcuts for highlight actions.
"""

import sys
from aqt import mw
from aqt.utils import tooltip

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QCursor
except ImportError:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QCursor

from .key_recorder import KeyRecorderMixin


class QuickActionsSettingsView(KeyRecorderMixin, QWidget):
    """View for configuring quick action keyboard shortcuts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_panel = parent
        self.recording_target = None  # 'add_to_chat' or 'ask_question'

        # Initialize key recorder
        self.setup_key_recorder()

        # Load current shortcuts from config
        config = mw.addonManager.getConfig(__name__)
        self.shortcuts = config.get("quick_actions", {
            "add_to_chat": {"keys": ["Meta", "F"]},
            "ask_question": {"keys": ["Meta", "R"]}
        })

        self.setup_ui()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #1e1e1e; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: #1e1e1e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(24)

        # Header
        header = QLabel("Quick Actions")
        header.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        """)
        content_layout.addWidget(header)

        # Description
        desc = QLabel("Configure keyboard shortcuts for text highlighting actions")
        desc.setStyleSheet("""
            color: #9ca3af;
            font-size: 13px;
            margin-bottom: 8px;
        """)
        desc.setWordWrap(True)
        content_layout.addWidget(desc)

        # Add to Chat shortcut
        add_to_chat_label = QLabel("Add to Chat")
        add_to_chat_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(add_to_chat_label)

        self.add_to_chat_display = QPushButton()
        self.add_to_chat_display.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_to_chat_display.setFixedHeight(60)
        self._update_shortcut_display(self.add_to_chat_display, self.shortcuts["add_to_chat"]["keys"])
        self.add_to_chat_display.clicked.connect(lambda: self.start_recording('add_to_chat'))
        content_layout.addWidget(self.add_to_chat_display)

        add_to_chat_desc = QLabel("Directly add highlighted text to OpenEvidence chat")
        add_to_chat_desc.setStyleSheet("color: #6b7280; font-size: 11px; margin-bottom: 8px;")
        content_layout.addWidget(add_to_chat_desc)

        # Ask Question shortcut
        ask_question_label = QLabel("Ask Question")
        ask_question_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(ask_question_label)

        self.ask_question_display = QPushButton()
        self.ask_question_display.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ask_question_display.setFixedHeight(60)
        self._update_shortcut_display(self.ask_question_display, self.shortcuts["ask_question"]["keys"])
        self.ask_question_display.clicked.connect(lambda: self.start_recording('ask_question'))
        content_layout.addWidget(self.ask_question_display)

        ask_question_desc = QLabel("Open question input with highlighted text as context")
        ask_question_desc.setStyleSheet("color: #6b7280; font-size: 11px; margin-bottom: 8px;")
        content_layout.addWidget(ask_question_desc)

        content_layout.addStretch()

        # Save button at bottom
        save_btn = QPushButton("Save")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFixedHeight(44)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        save_btn.clicked.connect(self.save_shortcuts)
        content_layout.addWidget(save_btn)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _update_shortcut_display(self, button, keys):
        """Update a shortcut display button with current keys"""
        from .utils import format_keys_verbose

        if self.recording_target:
            # During recording
            if keys:
                display_text = format_keys_verbose(keys)
                button.setText(display_text)
                button.setStyleSheet("""
                    QPushButton {
                        background: #2c2c2c;
                        color: #3b82f6;
                        border: 2px solid #3b82f6;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                """)
            else:
                button.setText("Press any key combination...")
                button.setStyleSheet("""
                    QPushButton {
                        background: #2c2c2c;
                        color: #3b82f6;
                        border: 2px solid #3b82f6;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                """)
        else:
            # Normal state
            if keys:
                display_text = format_keys_verbose(keys)
                button.setText(display_text)
            else:
                button.setText("Click to record shortcut")

            button.setStyleSheet("""
                QPushButton {
                    background: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #333333;
                    border-color: #3b82f6;
                }
            """)

    def start_recording(self, target):
        """Start recording keys for a specific shortcut"""
        self.recording_target = target

        # Update display to show recording state
        if target == 'add_to_chat':
            self._update_shortcut_display(self.add_to_chat_display, [])
        else:
            self._update_shortcut_display(self.ask_question_display, [])

        # Start the key recorder from mixin
        super().start_recording()

    def _update_recording_display(self, keys):
        """Called by KeyRecorderMixin during recording to update the display"""
        if self.recording_target == 'add_to_chat':
            self._update_shortcut_display(self.add_to_chat_display, keys)
        else:
            self._update_shortcut_display(self.ask_question_display, keys)

    def _on_keys_recorded(self, keys):
        """Called by KeyRecorderMixin when recording is complete"""
        if not self.recording_target:
            return

        # Save the recorded keys
        if keys:
            self.shortcuts[self.recording_target]["keys"] = keys

        # Update displays with final keys
        if self.recording_target == 'add_to_chat':
            self._update_shortcut_display(self.add_to_chat_display, self.shortcuts["add_to_chat"]["keys"])
        else:
            self._update_shortcut_display(self.ask_question_display, self.shortcuts["ask_question"]["keys"])

        self.recording_target = None

    def save_shortcuts(self):
        """Save shortcuts to config"""
        config = mw.addonManager.getConfig(__name__)
        config["quick_actions"] = self.shortcuts
        mw.addonManager.writeConfig(__name__, config)

        # Show success message with instruction
        tooltip("Quick Actions shortcuts saved!\n\nReview a new flashcard to see the updated shortcuts.", period=3000)

        # Navigate back to home
        if self.parent_panel and hasattr(self.parent_panel, 'show_home_view'):
            self.parent_panel.show_home_view()
