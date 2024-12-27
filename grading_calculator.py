import sys
from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from scene.interactive_scene import InteractiveScene
from view.ZoomableView import ZoomableView

# Get the current directory of the script
# define the relative path to the image
image_path = Path(__file__).parent / "test_diagram.jpg"


class GradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Landscape Grading Calculator")
        self.initUI()

    def initUI(self):
        # Set the window title and dimensions
        self.setWindowTitle("Main Window with Canvas")

        # Create the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Set up the layout
        layout = QVBoxLayout(central_widget)

        # Create a QGraphicsView and QGraphicsScene for the blank canvas
        self.canvas = ZoomableView()

        self.scene = InteractiveScene()
        # Set a .jpg image as the background
        pixmap = QPixmap(str(image_path))

        # Get the dimensions of the image
        image_width = pixmap.width()
        image_height = pixmap.height()

        # Resize the window to match the image dimensions
        self.resize(image_width, image_height)

        # Set the scaled pixmap as the background brush
        self.scene.addPixmap(pixmap)

        self.canvas.setScene(self.scene)

        # Add the canvas to the layout
        layout.addWidget(self.canvas)

        # Add a button to increment label values
        # self.increment_button = QPushButton("Increment Heights")
        # layout.addWidget(self.increment_button)

        # Connect the button click to the increment_heights method
        # self.increment_button.clicked.connect(self.scene.increment_heights)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = GradingApp()
    main_window.show()
    sys.exit(app.exec_())
