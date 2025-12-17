import os
import re
import aqt
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.qt import QDockWidget, QVBoxLayout, Qt, QUrl, QWidget, QHBoxLayout, QPushButton, QLabel, QCursor, QPainter
from aqt.utils import showInfo, tooltip

# Global reference to prevent garbage collection
dock_widget = None
current_card_text = ""  # Store the current card text for Tab key access

class CustomTitleBar(QWidget):
    """Custom title bar with pointer cursor on buttons"""
    def __init__(self, dock_widget, parent=None):
        super().__init__(parent)
        self.dock_widget = dock_widget
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 4, 4)
        layout.setSpacing(2)
        
        # Title label
        self.title_label = QLabel("OpenEvidence")
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 13px; font-weight: 500;")
        layout.addWidget(self.title_label)
        
        # Add stretch to push buttons to the right
        layout.addStretch()
        
        # Float/Undock button with high-quality SVG icon
        self.float_button = QPushButton()
        self.float_button.setFixedSize(24, 24)
        self.float_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Create high-resolution SVG icon for float button
        float_icon_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="36" height="36" stroke="white" stroke-width="3" fill="none" rx="3"/>
            <path d="M18 6 L18 18 L6 18" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M30 42 L30 30 L42 30" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        
        # Convert SVG to QIcon
        try:
            from PyQt6.QtGui import QIcon, QPixmap
            from PyQt6.QtCore import QByteArray, QSize
            from PyQt6.QtSvg import QSvgRenderer
        except ImportError:
            from PyQt5.QtGui import QIcon, QPixmap
            from PyQt5.QtCore import QByteArray, QSize
            from PyQt5.QtSvg import QSvgRenderer
        
        # Render SVG at higher resolution for crisp display
        svg_bytes = QByteArray(float_icon_svg.encode())
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(48, 48)
        try:
            pixmap.fill(Qt.GlobalColor.transparent)
        except:
            pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        self.float_button.setIcon(QIcon(pixmap))
        self.float_button.setIconSize(QSize(14, 14))
        
        self.float_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.float_button.clicked.connect(self.toggle_floating)
        layout.addWidget(self.float_button)
        
        # Close button with high-quality SVG icon
        self.close_button = QPushButton()
        self.close_button.setFixedSize(24, 24)
        self.close_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Create high-resolution SVG icon for close button
        close_icon_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 8 L40 40 M40 8 L8 40" stroke="white" stroke-width="4" stroke-linecap="round"/>
        </svg>
        """
        
        # Render SVG at higher resolution for crisp display
        svg_bytes_close = QByteArray(close_icon_svg.encode())
        renderer_close = QSvgRenderer(svg_bytes_close)
        pixmap_close = QPixmap(48, 48)
        try:
            pixmap_close.fill(Qt.GlobalColor.transparent)
        except:
            pixmap_close.fill(Qt.transparent)
        painter_close = QPainter(pixmap_close)
        renderer_close.render(painter_close)
        painter_close.end()
        
        self.close_button.setIcon(QIcon(pixmap_close))
        self.close_button.setIconSize(QSize(14, 14))
        
        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
            }
        """)
        self.close_button.clicked.connect(self.dock_widget.hide)
        layout.addWidget(self.close_button)
        
        # Set background color for title bar - modern dark gray
        self.setStyleSheet("background: #2a2a2a; border-bottom: 1px solid rgba(255, 255, 255, 0.06);")
    
    def toggle_floating(self):
        self.dock_widget.setFloating(not self.dock_widget.isFloating())

class OpenEvidencePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtCore import QEvent
        except ImportError:
            try:
                from PyQt5.QtWebEngineWidgets import QWebEngineView
                from PyQt5.QtCore import QEvent
            except ImportError:
                # Fallback for some Anki versions where it's exposed differently or not available
                # But modern Anki should have it.
                from aqt.qt import QWebEngineView, QEvent

        self.web = QWebEngineView(self)
        layout.addWidget(self.web)
        
        # Install event filter after the page loads (when focusProxy is available)
        self.web.loadFinished.connect(self.install_event_filter)
        
        self.web.load(QUrl("https://www.openevidence.com/"))
    
    def install_event_filter(self):
        """Install event filter after page has loaded"""
        focus_proxy = self.web.focusProxy()
        if focus_proxy is not None:
            focus_proxy.installEventFilter(self)
    
    def eventFilter(self, source, event):
        """Catch Tab key press in the OpenEvidence webview"""
        try:
            from PyQt6.QtCore import QEvent, Qt
        except ImportError:
            from PyQt5.QtCore import QEvent, Qt
        
        if event.type() == QEvent.Type.KeyPress and source is self.web.focusProxy():
            # Check if Tab key is pressed (without Shift, Ctrl, Alt, or Cmd)
            if event.key() == Qt.Key.Key_Tab and not (event.modifiers() & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier)):
                # Get the stored card text
                global current_card_text
                if current_card_text:
                    # Fill the OpenEvidence search box with the card text
                    js_code = f"""
                    (function() {{
                        var searchInput = document.querySelector('input[placeholder*="medical"]') ||
                                        document.querySelector('input[placeholder*="question"]') ||
                                        document.querySelector('textarea[placeholder*="medical"]') ||
                                        document.querySelector('textarea[placeholder*="question"]') ||
                                        document.querySelector('input[type="text"]') ||
                                        document.querySelector('textarea');
                        
                        if (searchInput) {{
                            searchInput.value = `{current_card_text.replace('`', '\\`').replace('"', '\\"').replace('\\n', ' ')}`;
                            searchInput.focus();
                            searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }})();
                    """
                    self.web.page().runJavaScript(js_code)
                return True  # Consume the event
        
        return super().eventFilter(source, event)

def create_dock_widget():
    """Create the dock widget for OpenEvidence panel"""
    global dock_widget
    
    if dock_widget is None:
        # Create the dock widget
        dock_widget = QDockWidget("OpenEvidence", mw)
        dock_widget.setObjectName("OpenEvidenceDock")
        
        # Create the panel widget
        panel = OpenEvidencePanel()
        dock_widget.setWidget(panel)
        
        # Create and set custom title bar with pointer cursors
        custom_title = CustomTitleBar(dock_widget)
        dock_widget.setTitleBarWidget(custom_title)
        
        # Get config for width
        config = mw.addonManager.getConfig(__name__) or {}
        panel_width = config.get("width", 500)
        
        # Set initial size
        dock_widget.setMinimumWidth(300)
        dock_widget.resize(panel_width, mw.height())
        
        # Add the dock widget to the right side of the main window
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)
        
        # Hide by default
        dock_widget.hide()
        
        # Store reference to prevent garbage collection
        mw.openevidence_dock = dock_widget
    
    return dock_widget

def toggle_panel():
    """Toggle the OpenEvidence dock widget visibility"""
    global dock_widget
    
    if dock_widget is None:
        create_dock_widget()
    
    if dock_widget.isVisible():
        dock_widget.hide()
    else:
        # If the dock is floating, dock it back to the right side
        if dock_widget.isFloating():
            dock_widget.setFloating(False)
            mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)
        
        dock_widget.show()
        dock_widget.raise_()

def send_text_to_openevidence(text):
    """Send text to OpenEvidence search box"""
    global dock_widget
    
    if dock_widget is None:
        create_dock_widget()
    
    # Show the panel if it's hidden
    if not dock_widget.isVisible():
        toggle_panel()
    
    # Get the webview from the panel
    panel_widget = dock_widget.widget()
    if panel_widget and hasattr(panel_widget, 'web'):
        # JavaScript to fill the search input on OpenEvidence
        # This targets the main search/question input on the OpenEvidence homepage
        js_code = f"""
        (function() {{
            // Try to find the search input - OpenEvidence uses various selectors
            var searchInput = document.querySelector('input[placeholder*="medical"]') ||
                            document.querySelector('input[placeholder*="question"]') ||
                            document.querySelector('textarea[placeholder*="medical"]') ||
                            document.querySelector('textarea[placeholder*="question"]') ||
                            document.querySelector('input[type="text"]') ||
                            document.querySelector('textarea');
            
            if (searchInput) {{
                searchInput.value = `{text.replace('`', '\\`').replace('"', '\\"')}`;
                searchInput.focus();
                // Trigger input event in case the site listens for it
                searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }})();
        """
        panel_widget.web.page().runJavaScript(js_code)

def on_webview_did_receive_js_message(handled, message, context):
    if message == "openevidence":
        toggle_panel()
        return (True, None)
    elif message.startswith("oe_send_text:"):
        # Extract the text after the prefix
        text = message[13:]  # Remove "oe_send_text:" prefix
        send_text_to_openevidence(text)
        return (True, None)
    return handled

# Removed the bottom bar button - icon now appears in top toolbar only

def store_current_card_text(card):
    """Store the current card text globally for Tab key access from OpenEvidence panel"""
    global current_card_text
    
    # Get the text from the card - prefer answer if showing answer, otherwise question
    try:
        # Try to get the visible side
        if mw.reviewer and mw.reviewer.state == "answer":
            # Answer is showing
            text = card.answer()
        else:
            # Question is showing
            text = card.question()
        
        # Remove style tags and their contents first
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove script tags and their contents
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip remaining HTML tags
        text = re.sub('<[^<]+?>', '', text)
        
        # Decode HTML entities
        try:
            import html
            text = html.unescape(text)
        except:
            pass
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        current_card_text = text
    except:
        current_card_text = ""

def inject_tab_key_listener(html, card, context):
    """Inject JavaScript to listen for Tab key and send card text to OpenEvidence"""
    
    # Store the current card text whenever a card is shown
    store_current_card_text(card)
    
    # Only inject in the reviewer context
    if context != "reviewQuestion" and context != "reviewAnswer":
        return html
    
    # JavaScript to handle Tab key press
    tab_listener_js = """
    <script>
    (function() {
        document.addEventListener('keydown', function(event) {
            // Check if Tab key is pressed (without Shift, Ctrl, Alt, or Cmd)
            if (event.key === 'Tab' && !event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey) {
                event.preventDefault(); // Prevent default Tab behavior
                
                // Get the card text from the answer or question div
                var cardText = '';
                var answerDiv = document.querySelector('.answer') || document.querySelector('#answer');
                var questionDiv = document.querySelector('.question') || document.querySelector('#question') || document.querySelector('#qa');
                
                // Clone the element to avoid modifying the original
                var sourceElement = null;
                
                // Prefer answer if visible, otherwise use question
                if (answerDiv && answerDiv.offsetParent !== null) {
                    sourceElement = answerDiv.cloneNode(true);
                } else if (questionDiv) {
                    sourceElement = questionDiv.cloneNode(true);
                } else {
                    // Fallback: get all visible text from the card body
                    sourceElement = (document.querySelector('#qa') || document.body).cloneNode(true);
                }
                
                if (sourceElement) {
                    // Remove style and script tags from the clone
                    var styleTags = sourceElement.querySelectorAll('style, script');
                    styleTags.forEach(function(tag) { tag.remove(); });
                    
                    // Get the cleaned text
                    cardText = sourceElement.innerText || sourceElement.textContent;
                }
                
                // Clean up the text (remove extra whitespace)
                cardText = cardText.trim().replace(/\\s+/g, ' ');
                
                // Send to Python via pycmd
                if (cardText && typeof pycmd !== 'undefined') {
                    pycmd('oe_send_text:' + cardText);
                }
            }
        }, true); // Use capture phase to ensure we catch it first
    })();
    </script>
    """
    
    return html + tab_listener_js

def add_toolbar_button(links, toolbar):
    """Add OpenEvidence button to the top toolbar"""
    # Create open book SVG icon (matching Anki's icon size and style)
    open_book_icon = """
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -0.2em;">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
</svg>
"""

    # Add the button to the toolbar using Anki's standard hitem class
    links.append(
        f'<a class="hitem" href="#" onclick="pycmd(\'openevidence\'); return false;" title="OpenEvidence">{open_book_icon}</a>'
    )

# Hook registration
gui_hooks.webview_did_receive_js_message.append(on_webview_did_receive_js_message)

# Add toolbar button
gui_hooks.top_toolbar_did_init_links.append(add_toolbar_button)

# Initialize dock widget when main window is ready
gui_hooks.main_window_did_init.append(create_dock_widget)

# Inject Tab key listener into card reviewer and store current card text
gui_hooks.card_will_show.append(inject_tab_key_listener)

# Update stored card text when question/answer is shown
gui_hooks.reviewer_did_show_question.append(store_current_card_text)
gui_hooks.reviewer_did_show_answer.append(store_current_card_text)
