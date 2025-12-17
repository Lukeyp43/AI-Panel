import os
import aqt
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.qt import QDialog, QVBoxLayout, Qt, QUrl
from aqt.utils import showInfo, tooltip

# Global reference to prevent garbage collection
panel_instance = None

class OpenEvidenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OpenEvidence")
        
        # Configure window flags
        # Window makes it a standalone window
        # WindowStaysOnTopHint can be used if desired, but user didn't explicitly ask for it to be always on top, just "stay open"
        self.setWindowFlags(Qt.WindowType.Window)
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            try:
                from PyQt5.QtWebEngineWidgets import QWebEngineView
            except ImportError:
                # Fallback for some Anki versions where it's exposed differently or not available
                # But modern Anki should have it.
                from aqt.qt import QWebEngineView

        self.web = QWebEngineView(self)
        layout.addWidget(self.web)
        
        self.web.load(QUrl("https://www.openevidence.com/"))

    def load_config(self):
        config = mw.addonManager.getConfig(__name__) or {}
        self.panel_width = config.get("width", 500)
        self.height_percentage = config.get("height_percentage", 0.95)

    def show_side_panel(self):
        # Get screen geometry
        screen = self.screen()
        available_rect = screen.availableGeometry()
        
        height = int(available_rect.height() * self.height_percentage)
        width = self.panel_width
        
        # Position on the right side
        x = available_rect.width() - width - 20
        y = available_rect.top() + 10
        
        self.resize(width, height)
        self.move(x, y)
        
        self.show()
        self.raise_()
        self.activateWindow()

def toggle_panel():
    global panel_instance
    if not panel_instance:
        panel_instance = OpenEvidenceDialog(mw)
    
    if panel_instance.isVisible():
        if panel_instance.windowState() & Qt.WindowState.WindowMinimized:
             panel_instance.setWindowState(panel_instance.windowState() & ~Qt.WindowState.WindowMinimized)
        panel_instance.raise_()
        panel_instance.activateWindow()
    else:
        panel_instance.show_side_panel()

def on_webview_did_receive_js_message(handled, message, context):
    if message == "openevidence":
        toggle_panel()
        return (True, None)
    return handled

# Removed the bottom bar button - icon now appears in top toolbar only

def add_toolbar_button(links, toolbar):
    """Add OpenEvidence button to the top toolbar"""
    # Check for custom icon file
    addon_path = os.path.dirname(__file__)
    icon_path = os.path.join(addon_path, "icon.png")
    
    # Create button HTML
    if os.path.exists(icon_path):
        addon_name = os.path.basename(addon_path)
        icon_src = f"/_addons/{addon_name}/icon.png"
        icon_html = f'<img src="{icon_src}" style="width: 20px; height: 20px; vertical-align: middle;">'
    else:
        # Use book emoji as fallback
        icon_html = "📚"
    
    # Add the button link to the toolbar
    links.append(
        f'''
        <a class="hitem" href="#" onclick="pycmd('openevidence'); return false;" 
           title="OpenEvidence" style="display: inline-flex; align-items: center; padding: 0 6px;">
            {icon_html}
        </a>
        '''
    )

# Hook registration
gui_hooks.webview_did_receive_js_message.append(on_webview_did_receive_js_message)

# Add toolbar button
gui_hooks.top_toolbar_did_init_links.append(add_toolbar_button)
