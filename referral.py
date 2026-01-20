"""
Good Karma Referral Modal - "Shadow Tracking" implementation.
Shows to verified returning users (2+ days active, 2nd message of the day).
"""

from datetime import datetime
from aqt import mw

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QGraphicsDropShadowEffect
    from PyQt6.QtCore import Qt, QTimer, QByteArray, QPropertyAnimation, QRect, QEasingCurve, QRectF, QSize
    from PyQt6.QtGui import QCursor, QPixmap, QPainter, QColor, QBrush, QPalette, QPainterPath, QIcon
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QGraphicsDropShadowEffect
    from PyQt5.QtCore import Qt, QTimer, QByteArray, QPropertyAnimation, QRect, QEasingCurve, QRectF, QSize
    from PyQt5.QtGui import QCursor, QPixmap, QPainter, QColor, QBrush, QPalette, QPainterPath, QIcon
    from PyQt5.QtSvg import QSvgRenderer

ADDON_NAME = "the_ai_panel"

# Referral link (GitHub repo)
REFERRAL_LINK = "https://ankiweb.net/shared/info/1314683963"


import os

def get_referral_qr_path():
    """Get path to the bundled QR code image."""
    # Get the addon directory
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    qr_path = os.path.join(addon_dir, "referral_qr.png")
    
    if os.path.exists(qr_path):
        return qr_path
    else:
        print(f"AI Panel: QR code image not found at {qr_path}")
        return None


def should_show_referral() -> bool:
    """
    Check if we should show the referral modal.
    Trigger IF AND ONLY IF:
    1. Days Active >= 2 (used addon on 2+ distinct days)
    2. Just sent 2nd message today (messages == 2 in current session)
    3. Not shown yet (!has_shown_referral)
    """
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    analytics = config.get("analytics", {})
    
    # Check if already shown
    if analytics.get("has_shown_referral", False):
        return False
    
    # Check days active
    daily_usage = analytics.get("daily_usage", {})
    days_active = len(daily_usage.keys())
    
    if days_active < 2:
        return False
    
    # Check messages today
    today = datetime.now().strftime("%Y-%m-%d")
    todays_sessions = daily_usage.get(today, [])
    
    # Sum all messages across today's sessions
    messages_today = sum(session.get("messages", 0) for session in todays_sessions)
    
    # Trigger on exactly 2 messages (the moment they send their 2nd)
    if messages_today != 2:
        return False
    
    return True


def mark_referral_shown():
    """Mark that the referral modal has been shown."""
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    analytics = config.get("analytics", {})
    analytics["has_shown_referral"] = True
    analytics["referral_shown_date"] = datetime.now().isoformat()
    config["analytics"] = analytics
    mw.addonManager.writeConfig(ADDON_NAME, config)


def track_referral_modal(status: str, seconds_open: float):
    """
    Track referral modal interaction.
    
    Status can be:
    - "likely_scanned": Modal open > 10 seconds (assumed QR scan)
    - "explicit_reject": Clicked skip button
    - "ignored_quickly": Closed in < 10 seconds without action
    """
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    analytics = config.get("analytics", {})
    analytics["referral_modal_status"] = status
    analytics["referral_modal_seconds_open"] = round(seconds_open, 1)
    config["analytics"] = analytics
    mw.addonManager.writeConfig(ADDON_NAME, config)
    print(f"AI Panel: Referral modal tracked - {status} ({seconds_open:.1f}s)")


class RoundedQRLabel(QLabel):
    """QLabel that renders its pixmap with rounded corners."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        
    def paintEvent(self, event):
        if not self._pixmap:
            super().paintEvent(event)
            return
            
        try:
            from PyQt6.QtGui import QPainter, QPainterPath, QBrush
            from PyQt6.QtCore import Qt, QRectF
        except ImportError:
            from PyQt5.QtGui import QPainter, QPainterPath, QBrush
            from PyQt5.QtCore import Qt, QRectF
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, 20, 20)
        
        painter.setClipPath(path)
        
        # Draw white background first (for transparent parts of QR if any)
        painter.fillPath(path, QBrush(Qt.GlobalColor.white))
        
        # Draw the pixmap centered
        x = (self.width() - self._pixmap.width()) // 2
        y = (self.height() - self._pixmap.height()) // 2
        painter.drawPixmap(x, y, self._pixmap)


class ReferralOverlay(QWidget):
    """Good Karma referral overlay that covers the panel content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.open_time = datetime.now()
        # Import paint tools and animation
        try:
            from PyQt6.QtGui import QPainter, QColor, QBrush, QPalette
            from PyQt6.QtCore import Qt as QtCore, QPropertyAnimation, QRect, QEasingCurve
        except ImportError:
            from PyQt5.QtGui import QPainter, QColor, QBrush, QPalette
            from PyQt5.QtCore import Qt as QtCore, QPropertyAnimation, QRect, QEasingCurve
        
        self.animation = None
        self._bg_color = QColor("#1e1e1e")
        
        # Ensure the widget fills entirely
        self.setAutoFillBackground(True)
        
        # Install event filter on parent to catch resize events
        if parent:
            parent.installEventFilter(self)
        
        self.setup_ui()
    
    def eventFilter(self, watched, event):
        """Resize overlay when parent is resized."""
        try:
            from PyQt6.QtCore import QEvent
        except ImportError:
            from PyQt5.QtCore import QEvent
        
        if watched == self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parent().rect())
        return super().eventFilter(watched, event)
        
    def paintEvent(self, event):
        """Override paint to guarantee solid dark background."""
        try:
            from PyQt6.QtGui import QPainter
        except ImportError:
            from PyQt5.QtGui import QPainter
        
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._bg_color)
        painter.end()
        super().paintEvent(event)
        
    def showEvent(self, event):
        """Animate slide down when shown."""
        super().showEvent(event)
        self.animate_entry()

    def animate_entry(self):
        """Animate the overlay sliding down from the top."""
        try:
            from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve
        except ImportError:
            from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve
            
        parent = self.parent()
        if not parent:
            return
            
        end_rect = parent.rect()
        start_rect = QRect(end_rect.x(), -end_rect.height(), end_rect.width(), end_rect.height())
        
        self.setGeometry(start_rect)
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(1600)  # Slower slide-down (1.6 seconds)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.animation.start()
        
    def setup_ui(self):
        # Stylesheet for child widgets
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
            }
            QLabel {
                color: #FFFFFF;
                background: transparent;
            }
        """)
        
        # Track animation state
        self.exit_method = None
        self.typing_index = 0
        self.current_text = ""
        self.is_deleting = False
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add top spacing
        main_layout.addSpacing(80)
        
        # Content container (left-aligned text)
        container = QWidget()
        container.setMaximumWidth(380)
        container.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(28, 0, 28, 0)
        content_layout.setSpacing(0)
        
        # === ANIMATED TEXT LABELS ===
        
        # Intro label (will type then delete)
        self.intro_label = QLabel("")
        self.intro_label.setFixedHeight(30)  # Fixed height prevents resizing/flicker
        self.intro_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: #a3a3a3;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        """)
        self.intro_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.intro_label.setWordWrap(False)  # Keep on single line
        content_layout.addWidget(self.intro_label)
        
        content_layout.addSpacing(8)
        
        # Headline (hidden initially, revealed after intro deletes)
        self.headline_label = QLabel("")
        self.headline_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            color: #FFFFFF;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        """)
        self.headline_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headline_label.setWordWrap(True)
        self.headline_label.hide()
        content_layout.addWidget(self.headline_label)
        
        content_layout.addSpacing(12)
        
        # Body text (hidden initially)
        self.body_label = QLabel("")
        self.body_label.setStyleSheet("""
            font-size: 14px;
            color: #a3a3a3;
        """)
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.body_label.setWordWrap(True)
        self.body_label.hide()
        content_layout.addWidget(self.body_label)
        
        content_layout.addSpacing(12)
        
        # Instruction text (hidden initially)
        self.instruction_label = QLabel("")
        self.instruction_label.setStyleSheet("""
            font-size: 14px;
            color: #a3a3a3;
        """)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.hide()
        content_layout.addWidget(self.instruction_label)
        
        content_layout.addSpacing(30)
        
        # === QR CODE (hidden initially) ===
        self.qr_container = QWidget()
        self.qr_container.hide()
        
        qr_wrapper = QWidget()
        qr_wrapper.setFixedSize(150, 150)
        qr_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        qr_wrapper.setGraphicsEffect(shadow)
        
        qr_wrapper_layout = QVBoxLayout(qr_wrapper)
        qr_wrapper_layout.setContentsMargins(10, 10, 10, 10)
        
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(130, 130)
        self.qr_label.setStyleSheet("background: transparent;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        qr_path = get_referral_qr_path()
        if qr_path:
            pixmap = QPixmap(qr_path)
            self.qr_label.setPixmap(pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        qr_wrapper_layout.addWidget(self.qr_label)
        
        qr_center_layout = QHBoxLayout(self.qr_container)
        qr_center_layout.setContentsMargins(0, 0, 0, 0)
        qr_center_layout.addStretch()
        qr_center_layout.addWidget(qr_wrapper)
        qr_center_layout.addStretch()
        content_layout.addWidget(self.qr_container)
        
        content_layout.addSpacing(30)
        
        # === BUTTONS (shown with QR, but done button starts locked) ===
        self.btn_container = QWidget()
        self.btn_container.hide()
        btn_layout = QVBoxLayout(self.btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        
        # Done button - starts LOCKED with SVG lock icon
        self.done_btn = QPushButton(" Claim Good Luck")
        self.done_btn.setEnabled(False)  # Disabled initially
        self.done_btn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
        
        # Create high-def lock icon from SVG
        lock_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#888888">
            <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
        </svg>'''
        svg_bytes = QByteArray(lock_svg.encode())
        renderer = QSvgRenderer(svg_bytes)
        # Render at high resolution (48x48) for crispness
        pixmap = QPixmap(48, 48)
        try:
            pixmap.fill(Qt.GlobalColor.transparent)
        except:
            pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.lock_icon = QIcon(pixmap)
        self.done_btn.setIcon(self.lock_icon)
        self.done_btn.setIconSize(QSize(18, 18))
        
        self.done_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                color: #888888;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 14px 28px;
            }
        """)
        self.done_btn.clicked.connect(self.on_done_clicked)
        
        done_btn_wrapper = QWidget()
        done_btn_layout = QHBoxLayout(done_btn_wrapper)
        done_btn_layout.setContentsMargins(0, 0, 0, 0)
        done_btn_layout.addStretch()
        done_btn_layout.addWidget(self.done_btn)
        done_btn_layout.addStretch()
        btn_layout.addWidget(done_btn_wrapper)
        
        # Skip button
        self.skip_btn = QPushButton("Skip (and accept bad luck)")
        self.skip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #555555;
                border: none;
                font-size: 12px;
                padding: 8px;
            }
            QPushButton:hover {
                color: #888888;
            }
        """)
        self.skip_btn.clicked.connect(self.on_skip_clicked)
        btn_layout.addWidget(self.skip_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        
        content_layout.addWidget(self.btn_container)
        
        # Center container
        main_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignHCenter)
        main_layout.addStretch()
        
        # === START ANIMATION SEQUENCE (with delay) ===
        QTimer.singleShot(1200, self.start_typing_sequence)  # Wait 1200ms after slide-down
    
    def start_typing_sequence(self):
        """Begin the animated typing sequence."""
        self.intro_text = "Wait, I'm so sorry to interrupt..."
        self.headline_text = "Quick question... do you want to lock in good luck on your next exam?"
        self.body_text = "Please share this add-on with a friend or put it in your group chat for extra luck."
        self.instruction_text = "Scan with your phone. It pre-fills a text and just change the recipient to a friend and hit send. (The button below will unlock once you do)."
        
        # Phase 1: Type intro
        self.typing_index = 0
        self.current_target = self.intro_text
        self.current_label = self.intro_label
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_character)
        self.typing_timer.start(90)  # 90ms per character (slower, readable pace)
    
    def type_character(self):
        """Type one character at a time."""
        if self.is_deleting:
            # Backspace mode
            current = self.current_label.text()
            if len(current) > 0:
                self.current_label.setText(current[:-1])
            else:
                self.typing_timer.stop()
                self.is_deleting = False
                # Move to headline phase
                QTimer.singleShot(200, self.start_headline_phase)
        else:
            # Typing mode
            if self.typing_index < len(self.current_target):
                self.current_label.setText(self.current_target[:self.typing_index + 1])
                self.typing_index += 1
            else:
                self.typing_timer.stop()
                # If this was the intro, pause then delete
                if self.current_label == self.intro_label:
                    QTimer.singleShot(1500, self.start_backspace)  # 1.5s pause to read
                elif self.current_label == self.headline_label:
                    QTimer.singleShot(800, self.start_body_phase)
                elif self.current_label == self.body_label:
                    QTimer.singleShot(800, self.start_instruction_phase)
                elif self.current_label == self.instruction_label:
                    QTimer.singleShot(800, self.show_qr_code)
    
    def start_backspace(self):
        """Start deleting the intro text."""
        self.is_deleting = True
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_character)
        self.typing_timer.start(50)  # 50ms backspace
    
    def start_headline_phase(self):
        """Show and type headline."""
        self.intro_label.hide()
        self.headline_label.show()
        self.typing_index = 0
        self.current_target = self.headline_text
        self.current_label = self.headline_label
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_character)
        self.typing_timer.start(75)  # 75ms for headline
    
    def start_body_phase(self):
        """Show and type body text."""
        self.body_label.show()
        self.typing_index = 0
        self.current_target = self.body_text
        self.current_label = self.body_label
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_character)
        self.typing_timer.start(65)  # 65ms body text
    
    def start_instruction_phase(self):
        """Show and type instruction text."""
        self.instruction_label.show()
        self.typing_index = 0
        self.current_target = self.instruction_text
        self.current_label = self.instruction_label
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_character)
        self.typing_timer.start(70)  # 70ms instruction text
    
    def show_qr_code(self):
        """Show QR code and buttons (button starts locked)."""
        self.qr_container.show()
        self.btn_container.show()  # Show buttons immediately with QR
        
        # Unlock button after 12 seconds
        QTimer.singleShot(18000, self.unlock_button)  # 18 seconds
    
    def unlock_button(self):
        """Unlock the done button after 15 seconds."""
        self.done_btn.setEnabled(True)
        self.done_btn.setText("I sent it (Claim Good Luck)")
        self.done_btn.setIcon(QIcon())  # Remove lock icon
        self.done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.done_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 14px 28px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
    
    def show_buttons(self):
        """Show the action buttons (legacy, now handled in show_qr_code)."""
        self.btn_container.show()
    
    
    def on_skip_clicked(self):
        """Handle skip button click."""
        self.exit_method = "skip_button"
        self.close_overlay()
        
    def on_done_clicked(self):
        """Handle done button click."""
        self.exit_method = "done_button"
        self.close_overlay()
    
    def close_overlay(self):
        """Close the overlay and track interaction."""
        duration = (datetime.now() - self.open_time).total_seconds()
        
        status = "ignored_quickly"  # Default
        
        if self.exit_method == "skip_button":
            status = "explicit_reject"
        elif self.exit_method == "done_button":
            status = "referred"
        elif duration > 10:
            status = "likely_scanned"
            
        track_referral_modal(status, duration)
        
        # Hide and delete
        self.hide()
        self.deleteLater()


def show_referral_overlay_if_eligible(panel_widget):
    """Check eligibility and show overlay on the panel if appropriate."""
    if should_show_referral():
        # Mark as shown immediately to prevent re-triggers
        mark_referral_shown()
        
        # Create overlay as child of panel
        # IMPORTANT: Do NOT show immediately, let the animation handle it in showEvent
        overlay = ReferralOverlay(panel_widget)
        # Configure initial size but let animation handle position
        overlay.resize(panel_widget.size())
        overlay.show()
        overlay.raise_()
        return overlay
    return None

