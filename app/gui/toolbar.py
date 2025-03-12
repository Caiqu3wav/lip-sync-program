from PyQt5.QtWidgets import (QToolBar, QAction, 
                            QPushButton, QToolButton)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class ToolBar(QToolBar):
    def __init__(self):
        super().__init__("Main Toolbar")
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))
        
        # Add new project button
        self.new_project_btn = QToolButton()
        self.new_project_btn.setText("+")
        self.new_project_btn.setToolTip("New Project")
        self.addWidget(self.new_project_btn)
        
        self.addSeparator()
        
        # Add open project button
        self.open_action = QAction("🔍", self)
        self.open_action.setToolTip("Open Project")
        self.addAction(self.open_action)
        
        # Add settings button
        self.settings_action = QAction("⚙️", self)
        self.settings_action.setToolTip("Settings")
        self.addAction(self.settings_action)
        
        self.addSeparator()
        
        # Add process button
        self.process_btn = QPushButton("Process All")
        self.process_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 5px 15px;"
        )
        self.addWidget(self.process_btn)


# For testing the component individually
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)
    window = QMainWindow()
    toolbar = ToolBar()
    window.addToolBar(toolbar)
    window.resize(500, 100)
    window.show()
    sys.exit(app.exec_())