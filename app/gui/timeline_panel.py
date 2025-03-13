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
import subprocess
import os
from pathlib import Path
from utils.main import get_video_duration

class TimeLineTrack(QWidget):
    def __init__(self, name, color, video=None, audio_path=None):
        super().__init__()
        self.name = name
        self.video = video if video else None
        self.audio_path = audio_path if audio_path else None
        self.color = color
        self.duration = video.duration if video else None
        self.setFixedHeight(25)
        self.setMinimumWidth(340)

        if self.audio_path and self.video: 
            self.add_sync_button()

    def add_sync_button(self):
        """Adiciona um botão para sincronizar o áudio selecionado com o vídeo"""
        if not hasattr(self, 'sync_button'):
            self.sync_button = QPushButton("Sync with the video", self)
            self.sync_button.move(250, 0)
            self.sync_button.clicked.connect(self.sync_audio_with_video)


    def sync_audio_with_video(self, output_path):
        """ Sincroniza áudio e vídeo utilizando um script externo de lipsync. """
        video_path = self.video.path
        audio_path = self.audio_path
        print(f"Sincronizando {audio_path} com {video_path}...")

        ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # Voltar 3 níveis (de app.gui.timeline_panel para a raiz)

        inference_script = ROOT_DIR / "Wav2Lip" / "inference.py"
        model_path = ROOT_DIR / "app" / "core" / "wav2lip_gan.pth"

        if not inference_script.exists():
            print(f"Erro: Script de inferência não encontrado em {inference_script}")
            exit(1)

        if not model_path.exists():
            print(f"Erro: Modelo não encontrado em {model_path}")
            exit(1)
        
        command = [
            sys.executable, str(inference_script),
            "--checkpoint_path", str(model_path),
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", str(output_path)
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Lip sync concluído! Arquivo salvo em: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao sincronizar lipsync: {e}")
        except FileNotFoundError:
            print("Erro: Certifique-se de que o Python está no PATH e os arquivos existem.")


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#e6e6e6"))
        painter.setPen(QPen(QColor("#333333")))
        painter.drawText(10, 17, self.name)
        
        if self.video:
            painter.fillRect(60, 0, 200, self.height(), QColor(self.color))  # Representação visual
            painter.setPen(QPen(QColor(self.color).darker()))
            painter.drawRect(60, 0, 200, self.height() - 1)

    

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
        self.add_sync_all_button.clicked.connect(self.sync_multiple_audios_with_video)
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

    def sync_multiple_audios_with_video(self, video_path, output_path):
        """ Sincroniza áudio e vídeo utilizando um script externo de lipsync. """
        print(f"Sincronizando audios com {video_path}...")

        ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # Voltar 3 níveis (de app.gui.timeline_panel para a raiz)

        inference_script = ROOT_DIR / "Wav2Lip" / "inference.py"
        model_path = ROOT_DIR / "app" / "core" / "wav2lip_gan.pth"

        if not inference_script.exists():
            print(f"Erro: Script de inferência não encontrado em {inference_script}")
            exit(1)

        if not model_path.exists():
            print(f"Erro: Modelo não encontrado em {model_path}")
            exit(1)
        
        for i, audio in enumerate(self.audios):
            audio_path = audio.path
            output_path = Path(output_path) / f"synced_{i+1}.mp4"
            command = [
                sys.executable, str(inference_script),
                "--checkpoint_path", str(model_path),
                "--face", video_path,
                "--audio", audio_path,
                "--outfile", str(output_path)
            ]

            try:
                subprocess.run(command, check=True)
                print(f"Lip sync concluído para {audio_path}! Arquivo salvo em: {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"Erro ao sincronizar com audio {audio.path}, erro: {e}")
            except FileNotFoundError:
                print("Erro: Certifique-se de que o Python está no PATH e os arquivos existem.")
        
        print("Sincronização concluída para todos os áudios.")
        
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
    import os
    from PyQt5.QtWidgets import QApplication, QFileDialog
    from PyQt5.QtCore import QFileInfo
    
    app = QApplication(sys.argv)

    def sync_audio_with_video_override(video_path, audio_path, output_path):
        """ Sincroniza áudio e vídeo utilizando um script externo de lipsync. """
        print(f"Sincronizando {audio_path} com {video_path}...")

        ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # Voltar 3 níveis (de app.gui.timeline_panel para a raiz)

        inference_script = ROOT_DIR / "Wav2Lip" / "inference.py"
        model_path = ROOT_DIR / "app" / "core" / "wav2lip_gan.pth"

        if not inference_script.exists():
            print(f"Erro: Script de inferência não encontrado em {inference_script}")
            exit(1)

        if not model_path.exists():
            print(f"Erro: Modelo não encontrado em {model_path}")
            exit(1)
        
        command = [
            sys.executable, str(inference_script),
            "--checkpoint_path", str(model_path),
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", str(output_path)
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Lip sync concluído! Arquivo salvo em: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao sincronizar lipsync: {e}")
        except FileNotFoundError:
            print("Erro: Certifique-se de que o Python está no PATH e os arquivos existem.")


    def get_audio_duration(file_path):
        """ Obtém a duração do áudio utilizando ffmpeg. """
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-f", "null", "-"],
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            output = result.stderr

            for line in output.split("\n"):
                if "Duration:" in line:
                    duration_str = line.split("Duration: ")[1].split(",")[0]
                    h, m, s = map(float, duration_str.replace(":", " ").split())
                    return int(h * 3600 + m * 60 + s)

        except Exception as e:
            print(f"Erro ao obter duração do áudio: {e}")

        return 180  # Duração padrão

    # Selecionar vídeo
    video_path, _ = QFileDialog.getOpenFileName(None, "Selecione o Arquivo de Vídeo", "", "Vídeos (*.mp4 *.avi *.mov)")
    if not video_path:
        print("Nenhum vídeo selecionado.")
        sys.exit()

    # Selecionar áudio
    audio_path, _ = QFileDialog.getOpenFileName(None, "Selecione o Arquivo de Áudio", "", "Áudios (*.mp3 *.wav *.ogg)")
    if not audio_path:
        print("Nenhum áudio selecionado.")
        sys.exit()

    # Definir pasta de saída
    output_dir = QFileDialog.getExistingDirectory(None, "Selecione o Diretório de Saída")
    if not output_dir:
        print("Nenhum diretório de saída selecionado.")
        sys.exit()

        # Criar diretório padrão caso necessário
        # Garantir que o diretório de saída seja exatamente o desejado
    default_output_dir = Path(output_dir)

    # Definir caminho de saída diretamente dentro do output selecionado
    output_video_path = default_output_dir / f"synced_{QFileInfo(video_path).fileName()}"

    # Obter duração do áudio para referência
    audio_duration = get_audio_duration(audio_path)
    print(f"Duração do áudio: {audio_duration} segundos")

    # Sincronizar áudio e vídeo
    sync_audio_with_video_override(video_path, audio_path, output_video_path)

    sys.exit()