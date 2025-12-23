"""
Settings Editor View - Editor for a single keybinding.
"""

import sys
from aqt import mw
from aqt.utils import tooltip

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QCursor
except ImportError:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QCursor

from .settings_utils import ElidedLabel


class SettingsEditorView(QWidget):
    """View B: Editor for a single keybinding - drill-down view"""
    def __init__(self, parent=None, keybinding=None, index=None):
        super().__init__(parent)
        self.parent_panel = parent
        self.index = index  # None for new, number for edit
        self.keybinding = keybinding or {
            "name": "New Shortcut",
            "keys": [],
            "question_template": "Can you explain this to me:\nQuestion:\n{front}",
            "answer_template": "Can you explain this to me:\nQuestion:\n{front}\n\nAnswer:\n{back}"
        }
        self.recording_keys = False
        self.pressed_keys = []  # Use list to preserve key press order
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
        content_layout.setSpacing(20)

        # Section 1: Key Recorder
        key_label = QLabel("Shortcut Key")
        key_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        content_layout.addWidget(key_label)

        self.key_display = QPushButton()
        self.key_display.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.key_display.setFixedHeight(60)
        self._update_key_display()
        self.key_display.clicked.connect(self.start_recording)
        content_layout.addWidget(self.key_display)

        # Section 2: Front Side Template
        # Row 1: Header (Label only)
        q_label = QLabel("Front Side Template")
        q_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(q_label)

        # Row 2: Input
        self.question_template = QTextEdit()
        self.question_template.setPlainText(self.keybinding.get("question_template", ""))
        self.question_template.setStyleSheet("""
            QTextEdit {
                background-color: #2c2c2c;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                color: white;
                font-size: 13px;
                font-family: Menlo, Monaco, 'Courier New', monospace;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #4b5563;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.question_template.setMinimumHeight(100)
        content_layout.addWidget(self.question_template)

        # Row 3: Footer (Helper text left, chips right)
        q_footer_layout = QHBoxLayout()
        q_footer_layout.setSpacing(8)
        q_footer_layout.setContentsMargins(0, 4, 0, 0)

        q_help = ElidedLabel("Only {front} is available.")
        q_help.setStyleSheet("color: #6b7280; font-size: 11px;")
        q_footer_layout.addWidget(q_help, 1)  # Stretch factor 1 to absorb flexible space

        q_front_chip = QPushButton("+ {front}")
        q_front_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        q_front_chip.setFixedHeight(24)
        q_front_chip.setMinimumWidth(75)
        q_front_chip.setStyleSheet("""
            QPushButton {
                background: #374151;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        q_front_chip.clicked.connect(lambda: self.insert_variable(self.question_template, "{front}"))
        q_footer_layout.addWidget(q_front_chip)

        content_layout.addLayout(q_footer_layout)

        # Section 3: Back Side Template
        # Row 1: Header (Label only)
        a_label = QLabel("Back Side Template")
        a_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(a_label)

        # Row 2: Input
        self.answer_template = QTextEdit()
        self.answer_template.setPlainText(self.keybinding.get("answer_template", ""))
        self.answer_template.setStyleSheet("""
            QTextEdit {
                background-color: #2c2c2c;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                color: white;
                font-size: 13px;
                font-family: Menlo, Monaco, 'Courier New', monospace;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #4b5563;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.answer_template.setMinimumHeight(100)
        content_layout.addWidget(self.answer_template)

        # Row 3: Footer (Helper text left, chips right)
        a_footer_layout = QHBoxLayout()
        a_footer_layout.setSpacing(8)
        a_footer_layout.setContentsMargins(0, 4, 0, 0)

        a_help = ElidedLabel("Both {front} and {back} are available.")
        a_help.setStyleSheet("color: #6b7280; font-size: 11px;")
        a_footer_layout.addWidget(a_help, 1)  # Stretch factor 1 to absorb flexible space

        a_front_chip = QPushButton("+ {front}")
        a_front_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        a_front_chip.setFixedHeight(24)
        a_front_chip.setMinimumWidth(75)
        a_front_chip.setStyleSheet("""
            QPushButton {
                background: #374151;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        a_front_chip.clicked.connect(lambda: self.insert_variable(self.answer_template, "{front}"))
        a_footer_layout.addWidget(a_front_chip)

        a_back_chip = QPushButton("+ {back}")
        a_back_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        a_back_chip.setFixedHeight(24)
        a_back_chip.setMinimumWidth(75)
        a_back_chip.setStyleSheet("""
            QPushButton {
                background: #374151;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        a_back_chip.clicked.connect(lambda: self.insert_variable(self.answer_template, "{back}"))
        a_footer_layout.addWidget(a_back_chip)

        content_layout.addLayout(a_footer_layout)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Bottom section with Save button
        bottom_section = QWidget()
        bottom_section.setStyleSheet("background: #1e1e1e; border-top: 1px solid rgba(255, 255, 255, 0.06);")
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(16, 12, 16, 12)

        # Save button (disabled by default until changes are made)
        self.save_btn = QPushButton("Save")
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.setFixedHeight(44)
        self.save_btn.setEnabled(False)  # Disabled by default
        self._update_save_button_style()
        self.save_btn.clicked.connect(self.save_and_go_back)
        bottom_layout.addWidget(self.save_btn)

        layout.addWidget(bottom_section)

        # Store initial state to detect changes
        self._initial_state = {
            'keys': self.keybinding.get('keys', []).copy() if self.keybinding.get('keys') else [],
            'question_template': self.keybinding.get('question_template', ''),
            'answer_template': self.keybinding.get('answer_template', '')
        }

        # Connect change signals
        self.question_template.textChanged.connect(self._on_change)
        self.answer_template.textChanged.connect(self._on_change)

    def _update_save_button_style(self):
        """Update save button appearance based on enabled state"""
        if self.save_btn.isEnabled():
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background: #3b82f6;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #2563eb;
                }
            """)
        else:
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background: #333333;
                    color: #666666;
                    border: 1px solid #444444;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)

    def insert_variable(self, text_edit, variable):
        """Insert a variable at the current cursor position in a QTextEdit"""
        cursor = text_edit.textCursor()
        cursor.insertText(variable)
        text_edit.setFocus()

    def _on_change(self):
        """Detect if any changes were made and enable/disable save button"""
        # Get current state
        current_keys = self.keybinding.get('keys', [])
        current_question = self.question_template.toPlainText()
        current_answer = self.answer_template.toPlainText()

        # Compare with initial state
        has_changes = (
            current_keys != self._initial_state['keys'] or
            current_question != self._initial_state['question_template'] or
            current_answer != self._initial_state['answer_template']
        )

        # Enable/disable save button
        self.save_btn.setEnabled(has_changes)
        self._update_save_button_style()

    def _update_key_display(self):
        """Update the key display button appearance"""
        from .utils import format_keys_verbose

        keys = self.keybinding.get("keys", [])
        if self.recording_keys:
            text = "Press any key combination..."
            style = """
                QPushButton {
                    background: #2c2c2c;
                    color: #3b82f6;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
            """
        elif keys:
            # Display keycaps
            text = format_keys_verbose(keys)
            style = """
                QPushButton {
                    background: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    border-color: #4b5563;
                }
            """
        else:
            text = "Click to set shortcut"
            style = """
                QPushButton {
                    background: #2c2c2c;
                    color: #9ca3af;
                    border: 1px dashed #374151;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    border-color: #4b5563;
                }
            """

        self.key_display.setText(text)
        self.key_display.setStyleSheet(style)

    def start_recording(self):
        """Start recording key presses"""
        self.recording_keys = True
        self.pressed_keys = []  # Use list to preserve key press order
        self._update_key_display()
        self.setFocus()

    def stop_recording(self):
        """Stop recording and save keys"""
        self.recording_keys = False
        if self.pressed_keys:
            # Keep the original order (don't sort)
            self.keybinding["keys"] = self.pressed_keys.copy()
        self._update_key_display()
        self._on_change()  # Check if changes were made

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

            # Auto-stop after 500ms, or immediately if we hit 3 keys
            if len(self.pressed_keys) > 0:
                if len(self.pressed_keys) >= 3:
                    # Stop immediately when we reach 3 keys
                    QTimer.singleShot(100, self.stop_recording)
                else:
                    # Otherwise wait 500ms for more keys
                    QTimer.singleShot(500, self.stop_recording)
        else:
            super().keyPressEvent(event)

    def discard_and_go_back(self):
        """Discard changes and return to list view without saving"""
        if self.parent_panel and hasattr(self.parent_panel, 'show_list_view'):
            self.parent_panel.show_list_view()

    def save_and_go_back(self):
        """Save changes and return to list view"""
        # Validate
        if not self.keybinding.get("keys"):
            tooltip("Please set a keyboard shortcut")
            return

        question_template = self.question_template.toPlainText().strip()

        # Only validation: {back} cannot be used in Front Side Template (back content isn't available yet)
        if "{back}" in question_template:
            tooltip("Front Side Template cannot use {back} - only {front} is available when viewing the question")
            return

        answer_template = self.answer_template.toPlainText().strip()

        # Check for duplicate keybindings
        config = mw.addonManager.getConfig(__name__) or {}
        keybindings = config.get("keybindings", [])
        current_keys = self.keybinding.get("keys", [])

        for i, kb in enumerate(keybindings):
            # Skip the current keybinding if we're editing
            if self.index is not None and i == self.index:
                continue

            # Check if keys match
            existing_keys = kb.get("keys", [])
            if existing_keys == current_keys:
                tooltip("This key combination is already in use by another shortcut")
                return

        # Save
        self.keybinding["question_template"] = question_template
        self.keybinding["answer_template"] = answer_template

        # Update config
        if self.index is None:
            # New keybinding
            keybindings.append(self.keybinding)
        else:
            # Edit existing
            keybindings[self.index] = self.keybinding

        config["keybindings"] = keybindings
        mw.addonManager.writeConfig(__name__, config)

        # Refresh JavaScript in panel
        self._refresh_panel_javascript()

        # Go back to list
        if self.parent_panel and hasattr(self.parent_panel, 'show_list_view'):
            self.parent_panel.show_list_view()

    def _refresh_panel_javascript(self):
        """Helper to refresh JavaScript in the main panel"""
        # Import here to avoid circular imports
        from . import dock_widget
        if dock_widget and dock_widget.widget():
            panel = dock_widget.widget()
            # Only update keybindings, don't re-inject the entire listener
            if hasattr(panel, 'update_keybindings_in_js'):
                panel.update_keybindings_in_js()
                # Also update card texts to match new keybindings
                if hasattr(panel, 'update_card_text_in_js'):
                    panel.update_card_text_in_js()
