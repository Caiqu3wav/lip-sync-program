from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, 
                             QSplitter, QInputDialog, QMessageBox, QApplication, QFileDialog, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys
import os

from app.gui.preview_panel import PreviewPanel
from app.gui.output_panel import OutputPanel
from app.gui.timeline_panel import TimelinePanel
from app.gui.toolbar import ToolBar
from app.gui.status_bar import StatusBar
from app.core.project_manager import ProjectManager, Project
from typing import Optional


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__( )

        self.setWindowIcon(QIcon("app/assets/icon.png"))
        self.setWindowTitle("Video Subtitle Automation")
        self.setMinimumSize(600, 300)

        self.project_manager = ProjectManager()
        self.current_project: Optional[Project] = None

        
        # Set up the main toolbar
        self.toolbar = ToolBar()
        self.addToolBar(self.toolbar)

        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.create_new_project)
        self.toolbar.addAction(new_project_action)
        
        # Set up the status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Main layout and widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Horizontal splitter for panels
        h_splitter = QSplitter(Qt.Horizontal)

        self.output_panel = OutputPanel() 
        h_splitter.addWidget(self.output_panel)

        # Vertical splitter for preview and timeline
        v_splitter = QSplitter(Qt.Vertical)

        # Pass the timeline panel to the preview panel
        self.timeline_panel = TimelinePanel()
        self.preview_panel = PreviewPanel(self.timeline_panel)
        v_splitter.addWidget(self.preview_panel)

        
        # Setting preview panel
        v_splitter.addWidget(self.timeline_panel)

        # Add the vertical splitter to the horizontal splitter
        h_splitter.addWidget(v_splitter)

        # Set the split sizes
        h_splitter.setSizes([200, 800])
        v_splitter.setSizes([400, 300])

        # Add the splitter to the main layout
        main_layout.addWidget(h_splitter)
        
        # Set the central widget
        self.setCentralWidget(main_widget)
        
        # Set up menus
        self._create_menus()

    def _create_menus(self):

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)

        # Add actions to file menu here
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        # Add actions to edit menu here
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        # Add actions to view menu here
        
        # Project menu
        project_menu = menu_bar.addMenu("&Project")
        # Add actions to project menu here
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        # Add actions to tools menu here

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        # Add actions to help menu here

    def update_current_project(self, project: Project):
        self.current_project = project
        self.setWindowTitle(f"Video Subtitle Automation - {self.current_project.name}")
        self.preview_panel.update_with_project(project=self.current_project)
        self.output_panel.update_with_project(project=self.current_project)
        self.timeline_panel.update_with_project(project=self.current_project)
    

    def create_new_project(self):
        name, ok = QInputDialog.getText(self, "Novo Projeto", "Nome do Projeto:")

        if not (ok and name):
            return False
        

        file_dialog = QFileDialog(self)
        video_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        
        if not video_path:
            return False

        if not os.path.exists(video_path):
            QMessageBox.critical(self, "Erro", f"Arquivo não encontrado: {video_path}")
            return False  
        
        try:
            self.current_project = self.project_manager.create_project(name, video_path)

            self.update_current_project(self.current_project)

            self.status_bar.set_status(f"Project created: {name} ({self.current_project.project_file_path})")
            return True
        except Exception as e:
            print(f"Erro ao criar o projeto: {e}")
            QMessageBox.critical(self, "Erro", f"Não foi possível criar o projeto: {str(e)}")
            return False
        
    
    def open_project(self):
        file_dialog = QFileDialog(self)
        project_file, _ = file_dialog.getOpenFileName(self, "Open Project File", "", "Project Files (*.vsa)")

        if not project_file:
            return False

        try:
            self.current_project = self.project_manager.open_project(project_file)

            self.setWindowTitle(f"Video Subtitle Automation - {self.current_project.name}")
            self.preview_panel.update_with_project(project=self.current_project)

            self.status_bar.set_status(f"Project opened: {self.current_project.name} ({project_file})")
            return True

        except Exception as e:
            print(f"Erro ao abrir o projeto: {e}")
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o projeto: {str(e)}")
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()

    sys.exit(app.exec_())