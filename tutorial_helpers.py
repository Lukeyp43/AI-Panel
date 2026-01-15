"""
Tutorial Helpers - Utility functions for target resolution

This module provides helper functions to locate and get coordinates/bounds
of various UI elements for tutorial coach marks.
"""

from PyQt6.QtCore import QPoint, QRect
from aqt import mw


def get_toolbar_icon_rect_async(callback):
    """
    Asynchronously get the rectangle of the AI Panel toolbar icon.

    Uses JavaScript to query the DOM for the button position.

    Args:
        callback: Function to call with QRect result (or None if not found)
    """
    if not mw or not mw.toolbar or not mw.toolbar.web:
        callback(None)
        return

    # JavaScript to get the AI Panel button's bounding box
    js_code = """
    (function() {
        // Find the link with onclick="pycmd('openevidence')"
        const links = document.querySelectorAll('a.hitem');
        for (const link of links) {
            if (link.onclick && link.onclick.toString().includes('openevidence')) {
                const rect = link.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            }
        }
        return null;
    })();
    """

    def on_result(result):
        if result:
            try:
                # Convert toolbar web view coordinates to global coordinates
                toolbar_global = mw.toolbar.web.mapToGlobal(QPoint(0, 0))
                rect = QRect(
                    int(toolbar_global.x() + result['x']),
                    int(toolbar_global.y() + result['y']),
                    int(result['width']),
                    int(result['height'])
                )
                callback(rect)
            except:
                callback(None)
        else:
            callback(None)

    mw.toolbar.web.page().runJavaScript(js_code, on_result)


def get_toolbar_icon_rect():
    """
    Synchronous fallback for toolbar icon rect (uses approximation).

    Note: This is a fallback. Prefer using get_toolbar_icon_rect_async for accuracy.

    Returns:
        QRect in global screen coordinates, or None if toolbar not available
    """
    if not mw or not mw.toolbar or not mw.toolbar.web:
        return None

    try:
        # Get toolbar's global position
        toolbar_global = mw.toolbar.web.mapToGlobal(QPoint(0, 0))
        toolbar_size = mw.toolbar.web.size()

        # Icon is on the left side of toolbar, approximate position
        # Create a larger target area to ensure we catch it
        icon_x = toolbar_global.x() + 10
        icon_y = toolbar_global.y() + 5

        return QRect(icon_x, icon_y, 50, toolbar_size.height() - 10)
    except:
        return None


def get_gear_button_widget():
    """
    Get the settings gear button widget from the panel title bar.

    Returns:
        QPushButton widget, or None if not available
    """
    try:
        from . import dock_widget

        if dock_widget and dock_widget.titleBarWidget():
            settings_button = dock_widget.titleBarWidget().settings_button
            if settings_button:
                return settings_button
    except:
        pass

    return None


def get_gear_button_rect():
    """
    Get the global rectangle of the settings gear button.

    Returns:
        QRect in global screen coordinates, or None if not available
    """
    widget = get_gear_button_widget()
    if widget is None:
        return None

    try:
        global_pos = widget.mapToGlobal(QPoint(0, 0))
        return QRect(global_pos, widget.size())
    except:
        return None


def get_reviewer_card_center():
    """
    Get the center point of the reviewer card area.

    Returns:
        QPoint in global screen coordinates, or None if reviewer not active
    """
    if not mw.reviewer or not mw.reviewer.web:
        return None

    try:
        # Get reviewer web view's global position
        global_pos = mw.reviewer.web.mapToGlobal(QPoint(0, 0))
        size = mw.reviewer.web.size()

        # Center horizontally, position near the top where flashcard text appears
        # Use height // 6 to get closer to the top where the question text is
        center_x = global_pos.x() + (size.width() // 2)
        center_y = global_pos.y() + (size.height() // 6)

        return QPoint(center_x, center_y)
    except:
        return None


def get_reviewer_card_rect():
    """
    Get a rectangular area in the center of the reviewer card.

    Returns:
        QRect in global screen coordinates, or None if reviewer not active
    """
    point = get_reviewer_card_center()
    if point is None:
        return None

    # Create a 200x150 rect centered on the point
    return QRect(point.x() - 100, point.y() - 75, 200, 150)


def get_panel_web_view():
    """
    Get the AI Panel panel's web view widget.

    Returns:
        QWebEngineView widget, or None if not available
    """
    try:
        from . import dock_widget

        if dock_widget:
            panel = dock_widget.widget()
            if panel and hasattr(panel, 'web'):
                return panel.web
    except:
        pass

    return None


def get_panel_global_pos():
    """
    Get the global position of the AI Panel panel.

    Returns:
        QPoint in global screen coordinates, or None if panel not available
    """
    try:
        from . import dock_widget

        if dock_widget:
            return dock_widget.mapToGlobal(QPoint(0, 0))
    except:
        pass

    return None


def get_chat_input_rect_async(callback):
    """
    Asynchronously get the rectangle of the chat input box in the panel.

    Uses JavaScript to query the DOM for the input element position.

    Args:
        callback: Function to call with QRect result (or None if not found)
    """
    web_view = get_panel_web_view()
    if web_view is None:
        callback(None)
        return

    # JavaScript to get input bounding box
    js_code = """
    (function() {
        const input = document.querySelector('input[placeholder*="medical"], input[type="text"]');
        if (input) {
            const rect = input.getBoundingClientRect();
            return {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            };
        }
        return null;
    })();
    """

    def on_result(result):
        if result:
            try:
                # Convert web view coordinates to global coordinates
                web_global = web_view.mapToGlobal(QPoint(0, 0))
                rect = QRect(
                    int(web_global.x() + result['x']),
                    int(web_global.y() + result['y']),
                    int(result['width']),
                    int(result['height'])
                )
                callback(rect)
            except:
                callback(None)
        else:
            callback(None)

    web_view.page().runJavaScript(js_code, on_result)


def get_panel_rect():
    """
    Get the rectangle of the entire panel.

    Returns:
        QRect in global screen coordinates, or None if panel not available
    """
    try:
        from . import dock_widget

        if dock_widget:
            global_pos = dock_widget.mapToGlobal(QPoint(0, 0))
            return QRect(global_pos, dock_widget.size())
    except:
        pass

    return None


def is_panel_visible():
    """
    Check if the AI Panel panel is currently visible.

    Returns:
        bool: True if panel is visible, False otherwise
    """
    try:
        from . import dock_widget

        if dock_widget:
            return dock_widget.isVisible()
    except:
        pass

    return False


def is_reviewer_active():
    """
    Check if the Anki reviewer is currently active (card being shown).

    Returns:
        bool: True if reviewer is active, False otherwise
    """
    return mw.reviewer is not None and mw.reviewer.web is not None
