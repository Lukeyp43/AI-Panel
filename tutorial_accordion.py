"""
Tutorial accordion widget that floats in the bottom left corner.
Shows after onboarding is complete to guide users through key features.
"""

import json
from aqt import mw
from aqt.qt import *

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                  QPushButton, QCheckBox, QFrame, QSizePolicy)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect
    from PyQt6.QtGui import QPainter, QCursor, QPixmap
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                  QPushButton, QCheckBox, QFrame, QSizePolicy)
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect
    from PyQt5.QtGui import QPainter, QCursor, QPixmap
    from PyQt5.QtSvg import QSvgRenderer


class WordWrapLabel(QLabel):
    """QLabel that properly handles word wrapping and height calculation"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

    def heightForWidth(self, width):
        """Calculate required height for given width with word wrapping"""
        if not self.text():
            return 0

        # Get font metrics
        fm = self.fontMetrics()

        # Calculate bounding rectangle for wrapped text
        try:
            # PyQt6
            flags = Qt.TextFlag.TextWordWrap
            rect = fm.boundingRect(QRect(0, 0, width, 10000), int(flags), self.text())
        except:
            # PyQt5
            flags = Qt.TextWordWrap
            rect = fm.boundingRect(0, 0, width, 10000, flags, self.text())

        return rect.height() + 8  # Add padding for better spacing

    def sizeHint(self):
        """Return size hint based on current width"""
        width = self.width() if self.width() > 0 else 300
        height = self.heightForWidth(width)
        return QSize(width, height)

    def minimumSizeHint(self):
        """Return minimum size hint"""
        return self.sizeHint()

    def hasHeightForWidth(self):
        """Enable height-for-width layout calculation"""
        return True


class AccordionItem(QWidget):
    """Single accordion item with icon, title, description, and collapsible tasks"""

    toggled = pyqtSignal()

    def __init__(self, icon_svg, title, description, tasks, parent=None):
        super().__init__(parent)
        self.icon_svg = icon_svg
        self.title_text = title
        self.description_text = description
        self.tasks_data = tasks
        self.is_expanded = False
        self.task_checkboxes = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # SECTION HEADER - Exact spacing and sizes
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent; border: none;")

        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(24, 16, 24, 16)  # 16px top padding (part of 36px total)
        header_layout.setSpacing(12)

        # Circle Icon Container (40x40)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setStyleSheet("background: #262626; border-radius: 20px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_icon()
        header_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Vertical Stack: Title + Subtitle
        text_stack = QWidget()
        text_stack.setFixedHeight(40)  # Match icon height
        text_layout = QVBoxLayout(text_stack)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        # Title (Medium weight, White, 16px) - aligned to top
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 500; background: transparent;")
        self.title_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignTop)

        # Spacer to push subtitle to bottom
        text_layout.addStretch(1)

        # Subtitle (Normal weight, neutral-400, 14px) - aligned to bottom
        self.subtitle_label = QLabel(self.description_text)
        self.subtitle_label.setStyleSheet("color: #a3a3a3; font-size: 14px; font-weight: 400; background: transparent;")
        self.subtitle_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.subtitle_label.setWordWrap(True)
        text_layout.addWidget(self.subtitle_label, 0, Qt.AlignmentFlag.AlignBottom)

        header_layout.addWidget(text_stack, 1)
        layout.addWidget(header_container)

        # Content container (always visible)
        self.content_widget = QWidget()
        self.content_widget.setVisible(True)
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 20)  # 20px bottom for spacing
        content_layout.setSpacing(0)

        if self.tasks_data:
            tasks_container = QWidget()
            tasks_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            tasks_layout = QVBoxLayout(tasks_container)
            # Align tasks with header icon center (24px left + 20px icon center = 44px)
            tasks_layout.setContentsMargins(44, 0, 24, 0)
            tasks_layout.setSpacing(0)

            for idx, task_data in enumerate(self.tasks_data):
                is_last = (idx == len(self.tasks_data) - 1)
                task_widget = self.create_task_widget(task_data, is_last)
                tasks_layout.addWidget(task_widget)

            content_layout.addWidget(tasks_container)

        layout.addWidget(self.content_widget)

    def create_task_widget(self, task_data, is_last=False):
        """Create a single task row - TREE/TIMELINE STYLE"""
        task_container = QWidget()
        task_container.setStyleSheet("background: transparent; border: none;")
        task_container.setMinimumHeight(40)

        # Main horizontal layout
        main_layout = QHBoxLayout(task_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # LEFT: Branch container (vertical + horizontal lines) - FIXED WITH LAYOUTS
        branch_container = QWidget()
        branch_container.setFixedWidth(20)
        branch_layout = QHBoxLayout(branch_container)
        branch_layout.setContentsMargins(0, 0, 0, 0)
        branch_layout.setSpacing(0)

        # Vertical line container
        vert_container = QWidget()
        vert_container.setFixedWidth(1)
        vert_layout = QVBoxLayout(vert_container)
        vert_layout.setContentsMargins(0, 0, 0, 0)
        vert_layout.setSpacing(0)

        # Top vertical line (before branch)
        top_line = QFrame()
        top_line.setFrameShape(QFrame.Shape.VLine)
        top_line.setStyleSheet("background-color: #3f3f46; border: none;")
        top_line.setFixedWidth(1)
        top_line.setMinimumHeight(8)
        vert_layout.addWidget(top_line)

        # Horizontal branch line
        horiz_line = QFrame()
        horiz_line.setFrameShape(QFrame.Shape.HLine)
        horiz_line.setStyleSheet("background-color: #3f3f46; border: none;")
        horiz_line.setFixedHeight(1)
        horiz_line.setFixedWidth(19)

        if not is_last:
            # Bottom vertical line (after branch) - only if not last item
            bottom_line = QFrame()
            bottom_line.setFrameShape(QFrame.Shape.VLine)
            bottom_line.setStyleSheet("background-color: #3f3f46; border: none;")
            bottom_line.setFixedWidth(1)
            vert_layout.addWidget(bottom_line)
            vert_layout.setStretch(1, 1)  # Bottom line expands

        branch_layout.addWidget(vert_container, 0, Qt.AlignmentFlag.AlignLeft)
        branch_layout.addWidget(horiz_line, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(branch_container, 0, Qt.AlignmentFlag.AlignTop)

        # CENTER: Circle indicator
        circle_label = QLabel()
        circle_label.setFixedSize(16, 16)
        circle_label.setStyleSheet("background: transparent;")

        if not hasattr(self, 'task_circles'):
            self.task_circles = []
        self.task_circles.append(circle_label)

        main_layout.addWidget(circle_label, 0, Qt.AlignmentFlag.AlignTop)

        # RIGHT: Task text
        task_label = QLabel(task_data["text"])
        task_label.setWordWrap(True)
        task_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        task_label.setStyleSheet("color: #FFFFFF; font-size: 13px; background: transparent; padding-top: 2px;")

        # Store data
        task_label.setProperty("task_data", task_data)
        task_label.setProperty("circle_label", circle_label)
        task_label.setProperty("container", task_container)

        # Make clickable
        task_label.mousePressEvent = lambda event, cl=circle_label, tl=task_label, tc=task_container: self.toggle_task(cl, tl, tc)

        main_layout.addWidget(task_label, 1, Qt.AlignmentFlag.AlignTop)

        # Store references
        checkbox_placeholder = QCheckBox()
        checkbox_placeholder.setVisible(False)
        checkbox_placeholder.setChecked(task_data["completed"])
        checkbox_placeholder.setProperty("circle_label", circle_label)
        checkbox_placeholder.setProperty("task_label", task_label)
        checkbox_placeholder.setProperty("container", task_container)
        self.task_checkboxes.append(checkbox_placeholder)

        # Set initial state
        self.update_task_appearance(circle_label, task_label, task_container, task_data["completed"])

        return task_container

    def toggle_task(self, circle_label, task_label, task_container):
        """Toggle task completion state"""
        # Find the corresponding checkbox
        for checkbox in self.task_checkboxes:
            if (checkbox.property("circle_label") == circle_label and
                checkbox.property("task_label") == task_label):
                # Toggle the checkbox
                new_state = not checkbox.isChecked()
                checkbox.setChecked(new_state)
                # Update appearance
                self.update_task_appearance(circle_label, task_label, task_container, new_state)
                self.on_task_changed()
                break

    def update_task_appearance(self, circle_label, task_label, task_container, is_completed):
        """Update the visual appearance of a task based on completion state"""
        if is_completed:
            # Completed state: Filled blue circle with checkmark
            filled_circle_svg = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="8" cy="8" r="8" fill="#2563EB"/>
                <path d="M5 8 L7 10 L11 6" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>"""
            self.set_svg_icon(circle_label, filled_circle_svg)

            # Strikethrough text and gray color
            task_label.setStyleSheet("color: #737373; font-size: 13px; background: transparent; padding-top: 2px; text-decoration: line-through;")
        else:
            # Uncompleted state: Empty gray circle outline
            empty_circle_svg = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="8" cy="8" r="7" fill="none" stroke="#525252" stroke-width="1.5"/>
            </svg>"""
            self.set_svg_icon(circle_label, empty_circle_svg)

            # Normal text - bright white for dark background
            task_label.setStyleSheet("color: #FFFFFF; font-size: 13px; background: transparent; padding-top: 2px;")

        # No border or background on container
        task_container.setStyleSheet("background: transparent; border: none;")

    def on_task_changed(self):
        self.update_icon()
        self.toggled.emit()

    def is_all_tasks_completed(self):
        if not self.task_checkboxes:
            return False
        return all(cb.isChecked() for cb in self.task_checkboxes)

    def get_completed_count(self):
        return sum(1 for cb in self.task_checkboxes if cb.isChecked())

    def get_total_count(self):
        return len(self.task_checkboxes)

    def toggle(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

    def collapse(self):
        """Explicitly collapse this item"""
        if self.is_expanded:
            self.is_expanded = False
            self.content_widget.setVisible(False)

    def update_icon(self):
        if self.is_all_tasks_completed():
            check_svg = """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="20" cy="20" r="20" fill="#2563EB"/>
                <path d="M13 20 L17 24 L27 14" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>"""
            self.set_svg_icon(self.icon_label, check_svg)
        else:
            # SVG icons at 40x40 with 20px icons inside (50% of container)
            svg_map = {
                "document": """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 12 L15 28 L25 28 L25 18 L21 12 Z M21 12 L21 18 L25 18" stroke="#a3a3a3" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>""",
                "search": """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="19" cy="19" r="6" stroke="#a3a3a3" stroke-width="1.5" fill="none"/>
                    <path d="M23.5 23.5 L26 26" stroke="#a3a3a3" stroke-width="1.5" stroke-linecap="round"/>
                </svg>""",
                "grid": """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="13" y="13" width="6" height="6" rx="1" stroke="#a3a3a3" stroke-width="1.5" fill="none"/>
                    <rect x="21" y="13" width="6" height="6" rx="1" stroke="#a3a3a3" stroke-width="1.5" fill="none"/>
                    <rect x="13" y="21" width="6" height="6" rx="1" stroke="#a3a3a3" stroke-width="1.5" fill="none"/>
                    <rect x="21" y="21" width="6" height="6" rx="1" stroke="#a3a3a3" stroke-width="1.5" fill="none"/>
                </svg>""",
                "settings": """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 14 L25 17 L25 23 L20 26 L15 23 L15 17 Z" stroke="#a3a3a3" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>"""
            }

            # Determine which icon to use based on title
            icon_key = "document"  # default
            if hasattr(self, 'title_text'):
                title_lower = self.title_text.lower()
                if "quick" in title_lower or "action" in title_lower:
                    icon_key = "search"
                elif "template" in title_lower or "shortcut" in title_lower:
                    icon_key = "grid"
                elif "setting" in title_lower or "customization" in title_lower:
                    icon_key = "settings"

            self.set_svg_icon(self.icon_label, svg_map.get(icon_key, svg_map["document"]))

    def set_svg_icon(self, label, svg_str):
        from aqt.qt import QByteArray
        svg_bytes = QByteArray(svg_str.encode())
        renderer = QSvgRenderer(svg_bytes)

        # Render at 5x resolution for ultra high quality, then scale down
        size = label.size()
        pixmap = QPixmap(size.width() * 5, size.height() * 5)
        try:
            pixmap.fill(Qt.GlobalColor.transparent)
        except:
            pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()

        # Scale down to actual size for smooth rendering
        scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)


class TutorialAccordion(QWidget):
    """Floating tutorial accordion in bottom left corner"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.accordion_items = []
        self.current_section_index = 0
        self.auto_advance_timer = None

        # Make this a floating widget
        try:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        except:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(420)
        self.setMaximumWidth(420)
        self.setMinimumHeight(400)  # Ensure enough height for content
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)

        self.setup_ui()
        self.position_bottom_left()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        # Container with border and shadow
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: #171717;
                border: 1px solid #262626;
                border-radius: 8px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)  # Lock header height
        header.setStyleSheet("background: transparent; border-bottom: 1px solid #262626;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(8)

        self.title_label = QLabel("Just one step ahead!")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 18px; background: transparent; border: none; outline: none;")
        self.title_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Navigation controls container
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        # Back button (ChevronLeft)
        self.back_btn = QPushButton()
        self.back_btn.setFixedSize(24, 24)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                outline: none;
                text-decoration: none;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover:enabled {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                opacity: 0.3;
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)
        back_svg = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 12 L6 8 L10 4" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""
        self.set_svg_icon(self.back_btn, back_svg, 16)
        self.back_btn.clicked.connect(self.go_back)
        nav_layout.addWidget(self.back_btn)

        # Forward button (ChevronRight)
        self.forward_btn = QPushButton()
        self.forward_btn.setFixedSize(24, 24)
        self.forward_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.forward_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                outline: none;
                text-decoration: none;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover:enabled {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                opacity: 0.3;
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)
        forward_svg = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 12 L10 8 L6 4" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""
        self.set_svg_icon(self.forward_btn, forward_svg, 16)
        self.forward_btn.clicked.connect(self.go_forward)
        nav_layout.addWidget(self.forward_btn)

        # Vertical divider
        divider = QFrame()
        divider.setFixedSize(1, 16)
        divider.setStyleSheet("background: #404040; border: none;")
        nav_layout.addWidget(divider)

        # Close/Skip button (X)
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                outline: none;
                text-decoration: none;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)
        close_svg = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4 L4 12 M4 4 L12 12" stroke="#A3A3A3" stroke-width="1.5" stroke-linecap="round"/>
        </svg>"""
        self.set_svg_icon(self.close_btn, close_svg, 16)
        self.close_btn.clicked.connect(self.skip_tutorial)
        nav_layout.addWidget(self.close_btn)

        header_layout.addWidget(nav_container)

        container_layout.addWidget(header)

        # Content
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Progress section
        progress_widget = QWidget()
        progress_widget.setFixedHeight(68)  # Lock progress height
        progress_widget.setStyleSheet("background: transparent; border-bottom: 1px solid #262626;")
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(24, 20, 24, 20)
        progress_layout.setSpacing(12)

        emoji_label = QLabel("👋")
        emoji_label.setStyleSheet("font-size: 24px; background: transparent; border: none; outline: none;")
        emoji_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        progress_layout.addWidget(emoji_label)

        progress_bar_container = QWidget()
        progress_bar_layout = QVBoxLayout(progress_bar_container)
        progress_bar_layout.setContentsMargins(0, 0, 0, 0)
        progress_bar_layout.setSpacing(0)

        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("background: #262626; border-radius: 4px;")

        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setFixedHeight(8)
        self.progress_fill.setStyleSheet("background: #404040; border-radius: 4px;")
        self.progress_fill.setFixedWidth(0)

        progress_bar_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(progress_bar_container, 1)  # Stretch to fill

        self.counter_label = QLabel("0/4")
        self.counter_label.setStyleSheet("color: #A3A3A3; font-size: 14px; background: transparent; border: none; outline: none;")
        self.counter_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        progress_layout.addWidget(self.counter_label)

        content_layout.addWidget(progress_widget)

        # Current section container (will be populated dynamically)
        self.section_container = QWidget()
        self.section_container.setStyleSheet("background: transparent;")
        self.section_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.section_layout = QVBoxLayout(self.section_container)
        self.section_layout.setContentsMargins(0, 0, 0, 0)
        self.section_layout.setSpacing(0)

        content_layout.addWidget(self.section_container)

        # Define all sections data
        self.sections_data = [
            {
                "icon": '<path d="M4 3 L4 17 L16 17 L16 7 L12 3 Z M12 3 L12 7 L16 7" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
                "title": "Getting Started",
                "description": "Open and close the OpenEvidence panel",
                "tasks": [
                    {"text": "Click the book icon 📖 in the Anki toolbar to open the OpenEvidence panel", "completed": False},
                    {"text": "Click the book icon again to close the panel", "completed": False}
                ]
            },
            {
                "icon": '<circle cx="10" cy="10" r="6" stroke="white" stroke-width="1.5" fill="none"/><path d="M14.5 14.5 L17.5 17.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>',
                "title": "Quick Actions",
                "description": "Highlight text and use quick actions on flashcards",
                "tasks": [
                    {"text": "Hold ⌘ (Cmd) and highlight text on a flashcard to trigger the Quick Actions bubble (Ctrl on Windows)", "completed": False},
                    {"text": "Click \"Add to Chat\" or press ⌘F (Ctrl+F on Windows) to add selected text to chat", "completed": False},
                    {"text": "Click the gear icon ⚙️ and navigate to \"Quick Actions\" settings to view or customize shortcuts", "completed": False}
                ]
            },
            {
                "icon": '<rect x="3" y="3" width="6" height="6" rx="1" stroke="white" stroke-width="1.5" fill="none"/><rect x="11" y="3" width="6" height="6" rx="1" stroke="white" stroke-width="1.5" fill="none"/><rect x="3" y="11" width="6" height="6" rx="1" stroke="white" stroke-width="1.5" fill="none"/><rect x="11" y="11" width="6" height="6" rx="1" stroke="white" stroke-width="1.5" fill="none"/>',
                "title": "Templates",
                "description": "Use keyboard shortcuts to populate search with card content",
                "tasks": [
                    {"text": "Open the panel, click in the search box, and press ⌘+Shift+S (Ctrl+Shift+S on Windows) to populate it with a template", "completed": False},
                    {"text": "Notice how the search box fills with formatted text from your current flashcard", "completed": False},
                    {"text": "Click the gear icon ⚙️ and navigate to \"Templates\" settings to view or edit all templates", "completed": False}
                ]
            },
            {
                "icon": '<path d="M10 3 L15 6.5 L15 13.5 L10 17 L5 13.5 L5 6.5 Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
                "title": "Settings & Customization",
                "description": "Explore and customize templates and quick actions",
                "tasks": [
                    {"text": "Click the gear icon ⚙️ in the panel title bar to open the settings home", "completed": False},
                    {"text": "Click on \"Templates\" to view and edit your template shortcuts", "completed": False},
                    {"text": "Click on \"Quick Actions\" to view and edit your highlight action shortcuts", "completed": False}
                ]
            }
        ]

        # Create all accordion items
        for item_data in self.sections_data:
            item = AccordionItem(
                item_data["icon"],
                item_data["title"],
                item_data["description"],
                item_data["tasks"]
            )
            item.toggled.connect(self.on_section_task_changed)
            self.accordion_items.append(item)
        container_layout.addWidget(self.content_widget)
        main_layout.addWidget(container)

        # Show the first section
        self.show_current_section()
        self.update_navigation_buttons()
        self.update_progress()

    def position_bottom_left(self):
        """Position widget in bottom left corner of Anki window"""
        if mw:
            # Get main window geometry
            mw_geometry = mw.geometry()

            # Position in bottom left of Anki window
            x = mw_geometry.x() + 16  # 16px from left edge
            bottom_offset = int(mw_geometry.height() * 0.35) + 800  # Move up 800px
            y = mw_geometry.y() + mw_geometry.height() - self.height() - bottom_offset

            # Safety check: ensure widget doesn't overflow top of window
            min_y = mw_geometry.y() + 60  # At least 60px from top (menu bar)
            y = max(y, min_y)

            self.move(x, y)

    def adjust_size(self):
        """Adjust widget size to fit content"""
        # Force all child widgets to recalculate their sizes
        for item in self.accordion_items:
            item.updateGeometry()
            if hasattr(item, 'content_widget'):
                item.content_widget.updateGeometry()

        # Force layout to recalculate (but don't call adjustSize - it constrains height)
        self.layout().activate()
        self.updateGeometry()

        # Reposition to ensure it stays in bottom left
        self.position_bottom_left()

    def show_current_section(self):
        """Display only the current section"""
        # Clear the section container
        while self.section_layout.count():
            child = self.section_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        # Add the current section (always visible, no toggle)
        if 0 <= self.current_section_index < len(self.accordion_items):
            current_item = self.accordion_items[self.current_section_index]
            # Make sure content is visible
            current_item.content_widget.setVisible(True)
            current_item.is_expanded = True
            self.section_layout.addWidget(current_item)

            # Resize widget to fit new content
            QTimer.singleShot(0, self.adjust_size)

    def get_max_accessible_section(self):
        """Find the furthest section user can navigate to (first incomplete section)"""
        for idx, item in enumerate(self.accordion_items):
            if not item.is_all_tasks_completed():
                return idx
        # All sections completed
        return len(self.accordion_items) - 1

    def update_navigation_buttons(self):
        """Enable/disable navigation buttons based on current state"""
        max_accessible = self.get_max_accessible_section()

        # Back button: can go back if not at first section
        can_go_back = self.current_section_index > 0
        self.back_btn.setEnabled(can_go_back)
        if can_go_back:
            self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.back_btn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

        # Forward button: can go forward up to max accessible section
        can_go_forward = self.current_section_index < max_accessible
        self.forward_btn.setEnabled(can_go_forward)
        if can_go_forward:
            self.forward_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.forward_btn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

    def go_back(self):
        """Navigate to previous section"""
        if self.current_section_index > 0:
            self.current_section_index -= 1
            self.show_current_section()
            self.update_navigation_buttons()
            self.update_progress()

    def go_forward(self):
        """Navigate to next section"""
        max_accessible = self.get_max_accessible_section()
        if self.current_section_index < max_accessible:
            self.current_section_index += 1
            self.show_current_section()
            self.update_navigation_buttons()
            self.update_progress()

    def skip_tutorial(self):
        """Skip/close the tutorial"""
        self.close()

    def on_section_task_changed(self):
        """Handle task completion - auto-advance if section is complete"""
        current_item = self.accordion_items[self.current_section_index]

        # Update navigation and progress
        self.update_navigation_buttons()
        self.update_progress()

        # Auto-advance if current section is complete and not the last section
        if current_item.is_all_tasks_completed() and self.current_section_index < len(self.accordion_items) - 1:
            # Cancel any existing timer
            if self.auto_advance_timer is not None:
                self.auto_advance_timer.stop()

            # Start new timer for auto-advance (500ms delay)
            self.auto_advance_timer = QTimer()
            self.auto_advance_timer.setSingleShot(True)
            self.auto_advance_timer.timeout.connect(self.auto_advance)
            self.auto_advance_timer.start(500)

    def auto_advance(self):
        """Automatically advance to next section"""
        if self.current_section_index < len(self.accordion_items) - 1:
            self.current_section_index += 1
            self.show_current_section()
            self.update_navigation_buttons()
            self.update_progress()

    def mark_task_complete(self, item_index, task_index):
        """Mark a specific task as complete"""
        if 0 <= item_index < len(self.accordion_items):
            item = self.accordion_items[item_index]
            if 0 <= task_index < len(item.task_checkboxes):
                checkbox = item.task_checkboxes[task_index]
                if not checkbox.isChecked():
                    checkbox.setChecked(True)
                    # Update the task appearance
                    circle_label = checkbox.property("circle_label")
                    task_label = checkbox.property("task_label")
                    task_container = checkbox.property("container")
                    if circle_label and task_label and task_container:
                        item.update_task_appearance(circle_label, task_label, task_container, True)
                    # Trigger update
                    self.on_section_task_changed()

    def handle_event(self, event_name):
        """Handle tutorial events to complete tasks"""
        event_mapping = {
            "panel_opened": (0, 0),        # Getting Started: open panel
            "panel_closed": (0, 1),        # Getting Started: close panel
            "text_highlighted": (1, 0),    # Quick Actions: highlight text
            "add_to_chat": (1, 1),         # Quick Actions: add to chat
            "shortcut_used": (2, 0),       # Templates: use shortcut
            "settings_opened": (3, 0)      # Settings: open settings
        }

        if event_name in event_mapping:
            item_idx, task_idx = event_mapping[event_name]
            self.mark_task_complete(item_idx, task_idx)

    def update_progress(self):
        # Count completed sections (not individual tasks)
        completed_sections = sum(1 for item in self.accordion_items if item.is_all_tasks_completed())
        total_sections = len(self.accordion_items)

        # Update counter display
        self.counter_label.setText(f"{completed_sections}/{total_sections}")

        # Update progress bar fill
        if total_sections > 0:
            percentage = (completed_sections / total_sections) * 100
        else:
            percentage = 0

        bar_width = self.progress_bar.width()
        fill_width = int(bar_width * (percentage / 100))
        self.progress_fill.setFixedWidth(fill_width)

        # Complete tutorial when all done
        if completed_sections == total_sections and total_sections > 0:
            QTimer.singleShot(1000, self.complete_tutorial)

    def complete_tutorial(self):
        """Mark tutorial as complete and hide"""
        try:
            config = mw.addonManager.getConfig(__name__) or {}
            config["tutorial_completed"] = True
            mw.addonManager.writeConfig(__name__, config)
            print("OpenEvidence: Tutorial completed!")
        except Exception as e:
            print(f"OpenEvidence: Error saving tutorial config: {e}")

        # Fade out and close
        self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self.update_progress)

    def set_svg_icon(self, widget, svg_str, size):
        from aqt.qt import QByteArray, QIcon
        svg_bytes = QByteArray(svg_str.encode())
        renderer = QSvgRenderer(svg_bytes)

        # Render at 5x resolution for ultra high quality
        pixmap = QPixmap(size * 5, size * 5)
        try:
            pixmap.fill(Qt.GlobalColor.transparent)
        except:
            pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()

        # Scale down to actual size for smooth rendering
        scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        if isinstance(widget, QPushButton):
            widget.setIcon(QIcon(scaled_pixmap))
            widget.setIconSize(QSize(size, size))
        else:
            widget.setPixmap(scaled_pixmap)


# Global reference to keep tutorial alive
_tutorial_accordion = None


def show_tutorial_accordion():
    """Show the tutorial accordion in bottom left"""
    global _tutorial_accordion

    if _tutorial_accordion is None:
        _tutorial_accordion = TutorialAccordion(mw)

    _tutorial_accordion.show()
    _tutorial_accordion.raise_()
    return _tutorial_accordion


def get_tutorial_accordion():
    """Get the tutorial accordion instance"""
    return _tutorial_accordion
