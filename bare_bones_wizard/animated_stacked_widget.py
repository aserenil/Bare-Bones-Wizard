# animated_stacked_widget.py
from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, Slot


class AnimatedStackedWidget(QStackedWidget):
    """
    A QStackedWidget that provides a sliding animation when changing pages.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 300  # milliseconds
        self.is_animating = False

    @Slot(int)
    def goto_page(self, next_index):
        """Animates the transition to the specified page index."""
        if self.is_animating or next_index == self.currentIndex():
            return

        self.is_animating = True
        current_index = self.currentIndex()
        current_widget = self.widget(current_index)
        next_widget = self.widget(next_index)

        if not current_widget or not next_widget:
            self.is_animating = False
            return

        width = self.width()
        # Determine animation direction
        if next_index > current_index:
            # Slide to the left (forward)
            start_pos_current = QPoint(0, 0)
            end_pos_current = QPoint(-width, 0)
            start_pos_next = QPoint(width, 0)
        else:
            # Slide to the right (backward)
            start_pos_current = QPoint(0, 0)
            end_pos_current = QPoint(width, 0)
            start_pos_next = QPoint(-width, 0)

        end_pos_next = QPoint(0, 0)

        # Ensure the next widget is visible and positioned off-screen before animation starts
        next_widget.setGeometry(0, 0, width, self.height())
        next_widget.move(start_pos_next)
        next_widget.show()
        next_widget.raise_()

        # Create animations for both widgets
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(self.animation_duration)
        anim_current.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_current.setStartValue(start_pos_current)
        anim_current.setEndValue(end_pos_current)

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self.animation_duration)
        anim_next.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_next.setStartValue(start_pos_next)
        anim_next.setEndValue(end_pos_next)

        # Group the animations to run in parallel
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(anim_current)
        self.animation_group.addAnimation(anim_next)

        # Connect the finished signal to a cleanup slot
        self.animation_group.finished.connect(lambda: self._on_animation_finished(next_index))

        self.animation_group.start()

    def _on_animation_finished(self, next_index):
        """Called after the animation completes to finalize the state."""
        # This is the crucial step: officially set the current index.
        # This will also emit the `currentChanged` signal that our main window uses.
        self.setCurrentIndex(next_index)
        self.is_animating = False

