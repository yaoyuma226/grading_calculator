from PySide6.QtCore import Qt
from PySide6.QtGui import QNativeGestureEvent
from PySide6.QtWidgets import QGraphicsView


class ZoomableView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom_factor = 1.05  # Zoom factor for wheel events
        self._current_scale = 1.0  # Keeps track of the current scale level
        self._min_scale = 0.4  # Minimum zoom level
        self._max_scale = 3.0  # Maximum zoom level

    def event(self, event):
        if (
            isinstance(event, QNativeGestureEvent)
            and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture
        ):
            self.zoomNativeEvent(event)
            return True
        return super().event(event)

    def zoomNativeEvent(self, event: QNativeGestureEvent):
        pinch_value = event.value()
        # Get the scroll delta for zooming
        # print(
        #     f"Pinch Gesture Event: pos{event.pos().x(), event.pos().y()} "
        #     f"value({pinch_value})"
        # )

        # Calculate the new scale level
        if pinch_value > 0:  # Zoom in
            zoom_factor = self._zoom_factor
        else:  # Zoom out
            zoom_factor = 1 / self._zoom_factor
        new_scale = self._current_scale * zoom_factor

        # Restrict zoom levels to avoid excessive zooming
        if self._min_scale <= new_scale <= self._max_scale:
            self.scale(zoom_factor, zoom_factor)  # Apply the zoom
            self._current_scale = new_scale
        else:
            event.ignore()  # Ignore excessive zoom gestures
