import os
import aqt
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.qt import QDockWidget, QVBoxLayout, Qt, QUrl, QWidget
from aqt.utils import showInfo, tooltip

# Global reference to prevent garbage collection
dock_widget = None

class OpenEvidencePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

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

# Initialize dock widget when main window is ready
gui_hooks.main_window_did_init.append(create_dock_widget)
