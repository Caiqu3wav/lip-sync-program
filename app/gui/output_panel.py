from PyQt5.QtWidgets import (QWidget, QVBoxLayout, 
                            QListWidget, QListWidgetItem, QGroupBox, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QFileDialog 
import os

class OutputPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)

        # Caixa de Grupo para Vídeos Gerados
        self.group_box = QGroupBox("Vídeos Gerados")
        group_layout = QVBoxLayout(self.group_box)

        self.video_list = QListWidget()
        self.video_list.setAlternatingRowColors(True)
        self.video_list.setStyleSheet("""
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E0E0E0;
            }
        """)

        group_layout.addWidget(self.video_list)

        # Botão para Abrir Pasta
        self.open_folder_button = QPushButton("Abrir Pasta")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        group_layout.addWidget(self.open_folder_button)

        layout.addWidget(self.group_box)

        # Exibir mensagem inicial
        self.show_placeholder_message()

    def show_placeholder_message(self):
        """Exibe uma mensagem padrão caso não haja vídeos na lista."""
        self.video_list.clear()
        placeholder = QListWidgetItem("Vídeos gerados aparecem aqui")
        placeholder.setFlags(Qt.ItemIsEnabled)  # Desativa seleção
        placeholder.setForeground(QBrush(QColor("#9E9E9E")))  # Cinza claro
        self.video_list.addItem(placeholder)

    def update_with_project(self, project):
        """Atualiza a aba com os vídeos processados do projeto."""
        self.video_list.clear()
        if project and hasattr(project, "generated_videos") and project.generated_videos:
            for video_path in project.generated_videos:
                file_name = os.path.basename(video_path)
                item = QListWidgetItem(file_name)
                item.setData(Qt.UserRole, video_path)
                item.setBackground(QBrush(QColor("#4CAF50")))  # Verde
                self.video_list.addItem(item)
        else:
            self.show_placeholder_message()

    def open_output_folder(self):
        """Abre a pasta onde os vídeos gerados são salvos."""
        output_dir = os.path.join(os.path.expanduser("~"), "Documents", "VideoSubtitleAutomation", "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)  # Garante que a pasta exista
        QFileDialog.getExistingDirectory(self, "Abrir Pasta de Vídeos", output_dir)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    panel = OutputPanel()
    panel.show()
    sys.exit(app.exec_())