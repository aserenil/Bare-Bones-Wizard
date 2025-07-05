# animated_stacked_widget.py
from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    Slot,
)
from PySide6.QtWidgets import QStackedWidget


class AnimatedStackedWidget(QStackedWidget):
    """
    A QStackedWidget that provides a sliding animation when changing pages.
    The animation logic is based on the user-provided file.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 300  # milliseconds
        self.animation_group = QParallelAnimationGroup(self)
        # Connect the finished signal to hide the old page.
        self.animation_group.finished.connect(self._on_animation_finished)
        self._previous_widget = None

    @Slot(int)
    def goto_page(self, next_index):
        """Animates the transition to the specified page index."""
        current_index = self.currentIndex()
        if next_index == current_index:
            return

        # This logic is from your provided file: if an animation is already
        # running, stop it immediately.
        if self.animation_group.state() == QAbstractAnimation.State.Running:
            self.animation_group.stop()

        current_widget = self.widget(current_index)
        next_widget = self.widget(next_index)

        if not current_widget or not next_widget:
            self.setCurrentIndex(next_index)
            return

        width = self.width()
        # Determine animation direction
        if next_index > current_index:
            # Slide to the left (forward)
            offset = width
        else:
            # Slide to the right (backward)
            offset = -width

        # Position the next widget off-screen to slide in
        next_widget.setGeometry(0, 0, width, self.height())
        next_widget.move(offset, 0)

        # This is a key part of the logic from your file:
        # Set the index immediately. This makes the new widget the "current" one
        # and emits the `currentChanged` signal that main.py uses.
        self.setCurrentIndex(next_index)

        # Create animations for both widgets
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(self.animation_duration)
        anim_current.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_current.setStartValue(QPoint(0, 0))
        anim_current.setEndValue(QPoint(-offset, 0))

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self.animation_duration)
        anim_next.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_next.setStartValue(QPoint(offset, 0))
        anim_next.setEndValue(QPoint(0, 0))

        # Group the animations to run in parallel
        self.animation_group.clear()  # Clear any previous animations
        self.animation_group.addAnimation(anim_current)
        self.animation_group.addAnimation(anim_next)

        # Keep track of the widget we need to hide after the animation
        self._previous_widget = current_widget

        self.animation_group.start()

    def _on_animation_finished(self):
        """Called after the animation completes to hide the old page."""
        if self._previous_widget:
            self._previous_widget.hide()
            self._previous_widget.move(0, 0)  # Reset position for next time
            self._previous_widget = None
