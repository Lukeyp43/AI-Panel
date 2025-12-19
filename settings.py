"""
Settings UI for the OpenEvidence add-on.
Contains the drill-down settings interface with list and editor views.
"""

from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit
    from PyQt6.QtCore import Qt, QTimer
except ImportError:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit
    from PyQt5.QtCore import Qt, QTimer

from .utils import format_keys_display, format_keys_verbose


class SettingsEditorView(QWidget):
    """View B: Editor for a single keybinding - drill-down view"""
    def __init__(self, parent=None, keybinding=None, index=None):
        super().__init__(parent)
        self.parent_panel = parent
        self.index = index  # None for new, number for edit
        self.keybinding = keybinding or {
            "name": "New Shortcut",
            "keys": [],
            "question_template": "Can you explain this to me:\nQuestion:\n{question}",
            "answer_template": "Can you explain this to me:\nQuestion:\n{question}\n\nAnswer:\n{answer}"
        }
        self.recording_keys = False
        self.pressed_keys = set()
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid rgba(255, 255, 255, 0.06);")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 14px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        back_btn.clicked.connect(self.save_and_go_back)
        header_layout.addWidget(back_btn)

        # Title
        title_label = QLabel("Edit Shortcut" if self.index is not None else "New Shortcut")
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 13px; font-weight: 500;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addWidget(header)

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

        # Section 2: Question Template
        q_label = QLabel("Question Context")
        q_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(q_label)

        self.question_template = QTextEdit()
        self.question_template.setPlainText(self.keybinding.get("question_template", ""))
        self.question_template.setStyleSheet("""
            QTextEdit {
                background: #2c2c2c;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: Menlo, Monaco, 'Courier New', monospace;
            }
        """)
        self.question_template.setMinimumHeight(100)
        content_layout.addWidget(self.question_template)

        q_help = QLabel("Use {question} to insert card content")
        q_help.setStyleSheet("color: #9ca3af; font-size: 11px;")
        content_layout.addWidget(q_help)

        # Section 3: Answer Template
        a_label = QLabel("Answer Context")
        a_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 12px;")
        content_layout.addWidget(a_label)

        self.answer_template = QTextEdit()
        self.answer_template.setPlainText(self.keybinding.get("answer_template", ""))
        self.answer_template.setStyleSheet("""
            QTextEdit {
                background: #2c2c2c;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: Menlo, Monaco, 'Courier New', monospace;
            }
        """)
        self.answer_template.setMinimumHeight(100)
        content_layout.addWidget(self.answer_template)

        a_help = QLabel("Use {question} and {answer} to insert card content")
        a_help.setStyleSheet("color: #9ca3af; font-size: 11px;")
        content_layout.addWidget(a_help)

        content_layout.addStretch()

        # Delete button at bottom
        config = mw.addonManager.getConfig(__name__) or {}
        keybindings = config.get("keybindings", [])
        can_delete = len(keybindings) > 1 and self.index is not None

        delete_btn = QPushButton("Delete Shortcut")
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setEnabled(can_delete)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {'#e74c3c' if can_delete else '#666666'};
                border: none;
                font-size: 13px;
                padding: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {'rgba(231, 76, 60, 0.1)' if can_delete else 'transparent'};
                border-radius: 4px;
            }}
        """)
        delete_btn.clicked.connect(self.delete_keybinding)
        content_layout.addWidget(delete_btn)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _update_key_display(self):
        """Update the key display button appearance"""
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
        self.pressed_keys = set()
        self._update_key_display()
        self.setFocus()

    def stop_recording(self):
        """Stop recording and save keys"""
        self.recording_keys = False
        if self.pressed_keys:
            self.keybinding["keys"] = sorted(list(self.pressed_keys))
        self._update_key_display()

    def keyPressEvent(self, event):
        """Capture key presses when recording"""
        if self.recording_keys:
            key = event.key()
            key_map = {
                Qt.Key.Key_Control if hasattr(Qt.Key, 'Key_Control') else Qt.Key_Control: "Control/Meta",
                Qt.Key.Key_Meta if hasattr(Qt.Key, 'Key_Meta') else Qt.Key_Meta: "Control/Meta",
                Qt.Key.Key_Shift if hasattr(Qt.Key, 'Key_Shift') else Qt.Key_Shift: "Shift",
                Qt.Key.Key_Alt if hasattr(Qt.Key, 'Key_Alt') else Qt.Key_Alt: "Alt",
            }

            if key in key_map:
                self.pressed_keys.add(key_map[key])
            elif event.text() and event.text().isprintable():
                self.pressed_keys.add(event.text().upper())

            # Auto-stop after 500ms
            if len(self.pressed_keys) > 0:
                QTimer.singleShot(500, self.stop_recording)
        else:
            super().keyPressEvent(event)

    def save_and_go_back(self):
        """Save changes and return to list view"""
        # Validate
        if not self.keybinding.get("keys"):
            tooltip("Please set a keyboard shortcut")
            return

        question_template = self.question_template.toPlainText().strip()
        if not question_template or "{question}" not in question_template:
            tooltip("Question template must contain {question}")
            return

        answer_template = self.answer_template.toPlainText().strip()
        if not answer_template or "{question}" not in answer_template:
            tooltip("Answer template must contain {question}")
            return

        # Save
        self.keybinding["question_template"] = question_template
        self.keybinding["answer_template"] = answer_template

        # Update config
        config = mw.addonManager.getConfig(__name__) or {}
        keybindings = config.get("keybindings", [])

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

    def delete_keybinding(self):
        """Delete this keybinding"""
        if self.index is None:
            return

        config = mw.addonManager.getConfig(__name__) or {}
        keybindings = config.get("keybindings", [])

        if len(keybindings) <= 1:
            tooltip("Cannot delete the last keybinding")
            return

        del keybindings[self.index]
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
            if hasattr(panel, 'inject_shift_key_listener'):
                panel.inject_shift_key_listener()


class SettingsListView(QWidget):
    """View A: List of keybindings - main settings view"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_panel = parent
        self.setup_ui()
        self.load_keybindings()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid rgba(255, 255, 255, 0.06);")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)

        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 13px; font-weight: 500;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.close_settings)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #1e1e1e; border: none; }")

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: #1e1e1e;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(16, 16, 16, 80)
        self.list_layout.setSpacing(12)

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

        # Add button (fixed at bottom)
        add_btn = QPushButton("+ Add Shortcut")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setFixedHeight(48)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #2c2c2c;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #374151;
                border-color: #4b5563;
            }
        """)
        add_btn.clicked.connect(self.add_keybinding)

        # Position add button at bottom
        add_btn_container = QWidget()
        add_btn_container.setStyleSheet("background: #1e1e1e; border-top: 1px solid rgba(255, 255, 255, 0.06);")
        add_btn_layout = QVBoxLayout(add_btn_container)
        add_btn_layout.setContentsMargins(16, 12, 16, 12)
        add_btn_layout.addWidget(add_btn)

        layout.addWidget(add_btn_container)

    def load_keybindings(self):
        """Load and display keybindings"""
        config = mw.addonManager.getConfig(__name__) or {}
        self.keybindings = config.get("keybindings", [])

        if not self.keybindings:
            self.keybindings = [{
                "name": "Default",
                "keys": ["Shift", "Control/Meta"],
                "question_template": "Can you explain this to me:\nQuestion:\n{question}",
                "answer_template": "Can you explain this to me:\nQuestion:\n{question}\n\nAnswer:\n{answer}"
            }]
            config["keybindings"] = self.keybindings
            mw.addonManager.writeConfig(__name__, config)

        self.refresh_list()

    def refresh_list(self):
        """Refresh the keybinding cards"""
        # Clear existing cards
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add cards for each keybinding
        for i, kb in enumerate(self.keybindings):
            card = self.create_keybinding_card(kb, i)
            self.list_layout.addWidget(card)

        self.list_layout.addStretch()

    def create_keybinding_card(self, kb, index):
        """Create a card widget for a keybinding"""
        card = QPushButton()
        card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        card.setFixedHeight(72)
        card.clicked.connect(lambda: self.edit_keybinding(index))

        # Create card layout
        card_widget = QWidget()
        card_layout = QHBoxLayout(card_widget)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(12)

        # Left: Keycaps
        keys_label = QLabel(format_keys_display(kb.get("keys", [])))
        keys_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
            font-family: Menlo, Monaco, 'Courier New', monospace;
        """)
        keys_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(keys_label)

        # Middle: Template preview
        template = kb.get("question_template", "")
        preview = template[:40] + "..." if len(template) > 40 else template
        preview_label = QLabel(preview.replace("\n", " "))
        preview_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        preview_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(preview_label, 1)

        # Right: Chevron
        chevron = QLabel(">")
        chevron.setStyleSheet("color: #9ca3af; font-size: 16px;")
        chevron.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(chevron)

        # Set the layout content as button background
        card.setLayout(card_layout)
        card.setStyleSheet("""
            QPushButton {
                background: #2c2c2c;
                border: 1px solid #374151;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background: #374151;
                border-color: #4b5563;
            }
        """)

        return card

    def add_keybinding(self):
        """Add a new keybinding"""
        if self.parent_panel and hasattr(self.parent_panel, 'show_editor_view'):
            self.parent_panel.show_editor_view(None, None)

    def edit_keybinding(self, index):
        """Edit a keybinding"""
        if self.parent_panel and hasattr(self.parent_panel, 'show_editor_view'):
            self.parent_panel.show_editor_view(self.keybindings[index].copy(), index)

    def close_settings(self):
        """Close settings and return to main view"""
        if self.parent_panel and hasattr(self.parent_panel, 'show_web_view'):
            self.parent_panel.show_web_view()
