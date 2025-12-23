"""
Utility classes for settings UI.
"""

try:
    from PyQt6.QtWidgets import QLabel, QSizePolicy
    from PyQt6.QtGui import QPainter
    from PyQt6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import QLabel, QSizePolicy
    from PyQt5.QtGui import QPainter
    from PyQt5.QtCore import Qt


class ElidedLabel(QLabel):
    """QLabel that automatically elides text with ... when space is tight"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        try:
            self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        except:
            # PyQt5 fallback
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def paintEvent(self, event):
        """Draw elided text"""
        painter = QPainter(self)
        metrics = painter.fontMetrics()

        # Get elide mode based on PyQt version
        try:
            elide_mode = Qt.TextElideMode.ElideRight
        except AttributeError:
            elide_mode = Qt.ElideRight

        # Use contentsRect to respect margins/padding from stylesheet
        rect = self.contentsRect()

        # Get elided text that fits in current width (accounting for padding)
        elided = metrics.elidedText(
            self.text(),
            elide_mode,
            rect.width()
        )

        # Draw the elided text within the content rect
        painter.drawText(rect, self.alignment(), elided)
