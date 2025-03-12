from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QGroupBox)
from PyQt5.QtCore import Qt

class ProjectPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)

        group_box = QGroupBox("Project Files")
        group_layout = QVBoxLayout(group_box)

        self.project_list = QListWidget()
        self.project_list.setAlternatingRowColors(True)

        self._add_example_items()

        group_layout.addWidget(self.project_list)

        layout.addWidget(group_box)


    def _add_example_items(self):
        items = [
            "video_main.mp4",
            "audio_en.mp3",
            "audio_es.mp3",
            "audio_fr.mp3"
        ]

        for item_text in items:
            item = QListWidgetItem(item_text)
            self.project_list.addItem(item)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    panel = ProjectPanel()
    panel.show()
    sys.exit(app.exec_())