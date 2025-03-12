import sys
import os
import vlc
import ctypes
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, 
                             QFrame, QToolBar, QAction,
                             QSlider)
from PyQt5.QtCore import Qt
from moviepy.video.io.VideoFileClip import VideoFileClip

class Video():
    def __init__(self, path, duration):
        self.path = path
        self.duration = duration

    def get_duration(self):
        try:
            with VideoFileClip(self.path) as video:
                return int(video.duration * 1000)  # Convert to milliseconds
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

class PreviewPanel(QWidget):
    def __init__(self, timeline_panel):
        super().__init__()

        self.timeline_panel = timeline_panel
        self.video_added = None
        
        self.setStyleSheet("""
             QWidget {
                background-color: #2c3e50;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#videoFrame {
                background-color: black;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QSlider::groove:horizontal {
                background: #34495e;
                height: 10px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                width: 18px;
                height: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }              
        """)

        self.layout = QVBoxLayout(self)

        self.video_frame = QFrame(self)
        self.video_frame.setObjectName("videoFrame")
        self.video_frame.setFrameShape(QFrame.StyledPanel)
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(300)
        self.layout.addWidget(self.video_frame)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # Integrar VLC ao QFrame
        if sys.platform.startswith('linux'):  # Para Linux
            self.media_player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":  # Para Windows
            self.media_player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":  # Para macOS
            self.media_player.set_nsobject(self.video_frame.winId())


        # Barra de ferramentas com controles do vídeo
        self.tool_bar = QToolBar("Video Controls")
        self.layout.addWidget(self.tool_bar)

        # Ações de controle do vídeo
        self.play_action = QAction("▶ Play", self)
        self.play_action.triggered.connect(self.play_video)

        self.pause_action = QAction("⏸ Pause", self)
        self.pause_action.triggered.connect(self.pause_video)

        # Slider de progresso do vídeo
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.set_position)

        # Slider de volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Adicionando elementos na toolbar
        self.tool_bar.addAction(self.play_action)
        self.tool_bar.addAction(self.pause_action)
        self.tool_bar.addWidget(self.slider)
        self.tool_bar.addWidget(self.volume_slider)
      

    def load_video(self, video_path):
        print(f"Carregando vídeo de: {video_path}")

        if not os.path.exists(video_path):
            print("Vídeo não encontrado.")
            return

        # Open video file
        self.media = self.instance.media_new(video_path)
        self.media_player.set_media(self.media)

        self.media.parse()
        self.media_player.play()
        self.media_player.set_pause(True)  # Começa pausado

        duration = self.media.get_duration()

        if duration <= 0:
            duration = 200

        self.video_added = Video(video_path, duration)

        self.timeline_panel.add_video_track(self.video_added)


    def play_video(self):
        self.media_player.play()

    def pause_video(self):
        self.media_player.pause()


    def set_position(self, position):
        self.media_player.set_position(position / 1000.0)


    def set_volume(self, volume):
        self.media_player.audio_set_volume(volume)

    def closeEvent(self, event):
        self.media_player.stop()
        event.accept()

    def update_with_project(self, project):
        if project and os.path.exists(project.video_path):
            self.load_video(project.video_path)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = PreviewPanel()
    window.show()
    sys.exit(app.exec_())