from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsProxyWidget,
    QGraphicsScene,
    QGraphicsTextItem,
    QLineEdit,
)
from util.math_utils import (
    distance,
    get_angle,
    get_arrow_head,
    calculate_gradient_descent
)

DESCENDENT = 1.0


class InteractiveScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None  # Stores the starting position for a drag
        self.temp_line = None  # Temporary line for arrow preview
        self.is_dragging = False  # Tracks whether the mouse is being dragged
        self.given_points = []
        self.given_heights = []
        self.result_points = []
        self.result_heights = []
        self.angles = []
        self.scale = 1.0

    def mousePressEvent(self, event):
        self.start_pos = event.scenePos()  # Record the start position
        self.is_dragging = False  # Reset dragging flag
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Handle dragging to preview the arrow
        if self.start_pos:
            end_pos = event.scenePos()
            d = distance(end_pos, self.start_pos)
            if d < 10:
                # Ignore a single click
                self.is_dragging = True  # Set dragging flag
                return

            # Create or update the temporary line
            if self.temp_line is None:
                line = QLineF(self.start_pos, end_pos)
                self.temp_line = QGraphicsLineItem(line)
                pen = QPen(QColor("gray"))
                pen.setStyle(Qt.DashLine)  # Dashed line for preview
                self.temp_line.setPen(pen)
                self.addItem(self.temp_line)
            else:
                self.temp_line.setLine(QLineF(self.start_pos, end_pos))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        end_pos = event.scenePos()
        d = distance(end_pos, self.start_pos or end_pos)
        # print(f"distance: {d}")
        if d < 10 or not self.is_dragging:
            if event.button() == Qt.LeftButton:
                # Draw a dot on a simple click
                self.draw_dot(end_pos)
            else:
                self.draw_dot(end_pos, "green")
        else:
            # Draw an arrow on drag-and-release
            self.draw_arrow(self.start_pos, end_pos)
            if self.result_heights:
                self.calculate_heights()

        # Clean up
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
        self.start_pos = None
        self.is_dragging = False
        super().mouseReleaseEvent(event)

    def draw_dot(self, pos, color="black"):
        x, y = pos.x(), pos.y()
        # Draw a dot (circle) at the clicked position
        radius = 5
        d = 2 * radius
        dot = QGraphicsEllipseItem(x - radius, y - radius, d, d)
        dot.setBrush(QBrush(QColor(color)))
        self.addItem(dot)

        # Handle the input when Enter is pressed
        if color == "black":
            self.given_points.append(pos)
            # Create an input box (QLineEdit as a widget on the scene)
            input_box = QLineEdit()
            input_box.setPlaceholderText("Enter a number...")
            input_box.setFixedWidth(80)

            # Add the input box as a proxy widget to the scene
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(input_box)
            proxy.setPos(pos.x() + 10, pos.y() - 20)
            self.addItem(proxy)

            input_box.setFocus()  # Set focus to the input box

            input_box.returnPressed.connect(
                lambda: self.add_label_to_dot(pos, input_box, proxy, color)
            )
        else:
            self.result_points.append(pos)
            self.show_label_to_dot(pos, "0.0", color)

    def show_label_to_dot(self, pos, value: str, color):
        """Show a label to the dot based on the input box value."""
        text_item = QGraphicsTextItem(str(value))
        text_item.setPos(pos.x() + 10, pos.y() - 20)
        text_item.setDefaultTextColor(QColor(color))
        self.addItem(text_item)
        self.result_heights.append(text_item)

    def calculate_heights(self):
        """calculate heights"""
        first_height = self.result_heights[0]
        height = calculate_gradient_descent(
            self.given_points[0], 
            self.result_points[0],
            float(self.given_heights[0].toPlainText()),
            self.angles[0],
            self.scale,
            DESCENDENT,
        )
        first_height.setPlainText(f"{height:.1f}")

    def add_label_to_dot(self, pos, input_box: QLineEdit, proxy, color):
        """Add a label to the dot based on the input box value."""
        # Get the value from the input box
        try:
            value = float(input_box.text())
        except ValueError:
            value = -1.0

        text_item = QGraphicsTextItem(str(value))
        text_item.setPos(pos.x() + 10, pos.y() - 20)
        if value == -1.0:
            color = "red"
        text_item.setDefaultTextColor(QColor(color))
        self.given_heights.append(text_item)
        self.addItem(text_item)

        # Remove the input box
        self.removeItem(proxy)
        proxy.widget().deleteLater()

    def draw_arrow(self, start_pos, end_pos):
        """Draw an arrow from the start position to the end position."""
        # Draw the arrow shaft (line)
        line = QGraphicsLineItem(QLineF(start_pos, end_pos))
        pen = QPen(QColor("black"))
        pen.setWidth(2)
        line.setPen(pen)
        self.addItem(line)

        if self.scale == 1:
            # 10 feet by pixel
            self.scale = 10 / distance(start_pos, end_pos)
            print(f"set scale to: {self.scale}")

        # Calculate the angle of the arrow
        angle = get_angle(start_pos, end_pos)
        self.angles.append(angle)
        # Create the arrowhead polygon
        arrow_head = get_arrow_head(angle, end_pos)
        arrow_item = QGraphicsPolygonItem(arrow_head)
        arrow_item.setBrush(QBrush(QColor("black")))
        self.addItem(arrow_item)
