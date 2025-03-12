from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from app.gui.main_window import MainWindow
import json
from app.core.project_manager import Project

class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.main_window = MainWindow()

        self.setWindowIcon(QIcon("app/assets/icon.png"))
        self.setWindowTitle("Bem-vindo")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Bem-vindo ao Video Subtitle Automation")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        btn_new_project = QPushButton("Novo Projeto")
        btn_new_project.clicked.connect(self.new_project)
        layout.addWidget(btn_new_project)

        btn_open_project = QPushButton("Abrir Projeto")
        btn_open_project.clicked.connect(self.open_project)
        layout.addWidget(btn_open_project)

    def new_project(self):
        """ Inicia um novo projeto e abre o editor """
        temp_window = MainWindow()
        sucess = temp_window.create_new_project()

        if sucess:
            self.main_window = temp_window
            self.main_window.show()
            self.close()
        else:
            del temp_window

    def open_project(self):
        """ Abre um projeto existente e abre o editor """
        project_file, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto", "C:/Users/lenovo-b40/Documents/VideoSubtitleAutomation", "Arquivos de Projeto (*.vsa);;Todos os Arquivos (*)"
        )

        if project_file:
           try:
                with open(project_file, 'r', encoding='utf-8') as file:
                    project_data = json.load(file)


                print(f"Projeto aberto: {project_file}")
                print("Dados do projeto:", project_data)
            
                project = Project(
                name=project_data['name'],
                video_path=project_data['video_path'],
                project_path=project_data['project_file_path']
                )

                # Restaurar outros atributos do projeto
                project.progress = project_data.get("progress", 0)
                project.configs = project_data.get("configs", {})
                project.languages = project_data.get("languages", [])
                project.audio_tracks = project_data.get("audio_tracks", [])

                self.main_window = MainWindow()
                self.main_window.update_current_project(project)
                self.main_window.show()

                self.close()

                return project
           
           except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Erro ao abrir o projeto: {e}")

        else:
            print("Nenhum projeto foi selecionado.")