from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QInputDialog, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QInputDialog
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from app.core.project_manager import Project
from app.gui.preview_panel import Video
from app.core.sync_engine import LipSyncEngine
import os

class TimeLineTrack(QWidget):
    def __init__(self, name, color, video=None, audios=None):
        super().__init__()
        self.name = name
        self.video = video
        self.audios = audios if audios else []
        self.color = color
        self.duration = video.duration if video else None
        self.setFixedHeight(25)
        self.setMinimumWidth(340)

        if self.audios and self.video: 
            self.add_sync_button()

    def add_sync_button(self):
        """Adiciona um botão para sincronizar o áudio selecionado com o vídeo"""
        if not hasattr(self, 'sync_button'):
            self.sync_button = QPushButton("Sync with the video", self)
            self.sync_button.move(250, 0)
            self.sync_button.clicked.connect(self.sync_audio_with_video)


    def sync_audio_with_video(self):
        """Chama o mecanismo de lip-sync para sincronizar áudio e vídeo"""
        print("Sincronizando áudio com o vídeo...")
        if not self.video:
            print("Nenhum vídeo presente para sincronizar.")
            return

        if not self.audios:
            print("Nenhum áudio selecionado.")
            return

        sync_engine = LipSyncEngine()

        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        output_dir = os.path.join(user_documents, "VideoSubtitleAutomation", "output")

        os.makedirs(output_dir, exist_ok=True)

        video_filename = os.path.basename(self.video.path).replace(".mp4", "_synced.mp4")
        output_path = os.path.join(output_dir, video_filename)

        sync_engine.generate_lip_sync(self.video.path, self.audios[0], output_path)

        print(f"Vídeo sincronizado salvo em: {output_path}")

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Desenhar fundo
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#e6e6e6"))

        # Desenhar rótulo
        painter.setPen(QPen(QColor("#333333")))
        painter.drawText(10, 17, self.name)

        # Desenhar o item da linha do tempo
        if self.duration and self.duration > 0:
            scale_factor = 0.1  # Ajuste conforme necessário
            item_width = int(self.duration * scale_factor)

            painter.fillRect(60, 0, item_width, self.height(), QColor(self.color))
            painter.setPen(QPen(QColor(self.color).darker()))
            painter.drawRect(60, 0, item_width, self.height() - 1)

    

class TimelinePanel(QWidget):
    def __init__(self):
        super().__init__() 
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Create a group box
        self.group_box = QGroupBox("Audios To Sync")
        self.group_layout = QVBoxLayout(self.group_box)
        self.tracks = []
        self.video = None
        self.audios = []
        self.add_audio_button = QPushButton("Add Audio")
        self.add_audio_button.clicked.connect(self.add_audio)
        self.group_layout.addWidget(self.add_audio_button)

        self.add_sync_all_button = QPushButton("Sync All Audios")
        self.group_layout.addWidget(self.add_sync_all_button)
        """ Add sync All function
        self.add_sync_all_button.clicked.connect(self.)
        """
        self.layout.addWidget(self.group_box)

    def add_video_track(self, video: Video):
        """Updates the timeline with the video track."""
        print(f"Adding video {video.path} duration: {video.duration}")
        # Remove old video track if exists
        for track in self.tracks:
            if track.name == "Video":
                self.group_layout.removeWidget(track)
                track.deleteLater()
                self.tracks.remove(track)
                break

        # Add new video track
        self.video = video

        duration = video.duration
        video_track = TimeLineTrack("Video", "#2196F3", video=video)
        video_track.duration = duration
        self.tracks.append((video_track, duration))
        self.layout.insertWidget(0, video_track)

    def _add_track(self, name, color, duration, audio_path):
        track = TimeLineTrack(name, color, video=self.video, audios=[audio_path])
        self.tracks.append(track)
        self.layout.insertWidget(len(self.tracks), track)
        self.audios.append(audio_path)
        
    def get_audio_duration(self, file_path):
            try:
                if file_path.lower().endswith('.mp3'):
                    audio = MP3(file_path)
                elif file_path.lower().endswith('.wav'):
                    audio = WAVE(file_path)
                elif file_path.lower().endswith('.ogg'):
                    audio = OggVorbis(file_path)
                else:
                    return 180

                return int(audio.info.length * 100)  # Convert to milliseconds
            except Exception as e:
                print(f"Error getting audio duration: {e}")
                return 180
        
    def add_audio(self):
            print(self.audios)
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.ogg)")
        
            if file_path:
                language, ok = QInputDialog.getText(self, "Add Language", "Enter the audio language name:")
                if ok and language.strip():
                    display_text = f"Audio ({language.strip()})"

                    duration = self.get_audio_duration(file_path)

                    color = f"#{hash(display_text) % 0xFFFFFF:06X}"
                    self._add_track(display_text, color, duration, file_path)
                    self.project.add_audio_track(file_path, language.strip(), duration)

    def update_with_project(self, project: Project):
        print("Updating timeline with project")
        """Atualiza a timeline com base nos dados do projeto"""
        self.project = project

        # Limpa trilhas existente
        for track in self.tracks:
            if isinstance(track, QWidget):  # Verifica se é realmente um QWidget
                self.group_layout.removeWidget(track)
                track.deleteLater()
            self.tracks.clear()

        # Adiciona trilhas de áudio do projeto
        for audio in self.project.audio_tracks:
            self._add_track(f"{audio['language']}", "#4CAF50", audio["duration"], audio["path"])

        self.update()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    panel = TimelinePanel()
    panel.show()
    sys.exit(app.exec_())