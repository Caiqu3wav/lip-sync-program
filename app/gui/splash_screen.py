from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer
import os


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("app/assets/icon.png"))
        self.setWindowTitle("Loading...")
        self.setStyleSheet("background-color: white;")
        self.setFixedSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel()
        icon.setPixmap(QPixmap("app/assets/icon.png").scaled(100,
    100, Qt.KeepAspectRatio))
        layout.addWidget(icon)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Ensure it refreshes

    QTimer.singleShot(4000, splash.close)  # Close after 4 seconds

    sys.exit(app.exec_())