import os
import uuid
import cv2
import json

class Project:
    def __init__(self, name: str, video_path, project_path):
        self.id = str(uuid.uuid4())
        self.name = name
        self.tracks = []
        self.audio_tracks = []
        self.video_path = video_path
        self.video_data = None
        self.languages = []

        if project_path:
            self.project_file_path = project_path
        else:
            self.project_file_path = os.path.join(os.path.expanduser("~"), "Documents", "VideoSubtitleAutomation", f"{name}.vsa")

        self.progress = 0
        self.configs = {}

    def add_audio_track(self, audio_path, language, duration):
        """Adiciona um novo áudio ao projeto"""
        self.audio_tracks.append({"path": audio_path, "language": language,  "duration": duration})
        self.save()
    

    def save(self):

        project_data = {
            "name": self.name,
            "video_path": self.video_path,
            "project_file_path": self.project_file_path,
            "progress": self.progress,
            "configs": self.configs,
            "languages": self.languages,
            "audio_tracks": self.audio_tracks
        }

        os.makedirs(os.path.dirname(self.project_file_path), exist_ok=True)
        
        with open(self.project_file_path, "w") as f:
            json.dump(project_data, f, indent=4)

        print(f"Projeto salvo com sucesso em: {self.project_file_path}")
    
    def set_progress(self, progress: int):
        self.progress = max(0, min(100, progress))

    def set_config(self, key: str, value):
        """Nova configuração do projeto adicionada"""
        self.configs[key] = value

    def get_config(self, key: str):
        """Retorna a configuração do projeto"""
        return self.configs.get(key, None)
    
class ProjectManager:
    def __init__(self):
        self.projects_dir = os.path.join(os.path.expanduser("~"), "Documents", "VideoSubtitleAutomation")
        os.makedirs(self.projects_dir, exist_ok=True)
        self.projects = {}


    def create_project(self, name, video_path) -> Project:
        project_path = os.path.join(self.projects_dir, f"{name}.vsa")
        if os.path.exists(project_path):
            raise FileExistsError(f"Project already exists: {project_path}")
        
        if not isinstance(video_path, str):
            raise ValueError("video_path must be a string.")
        
        project = Project(name, video_path, project_path)
        project.save()
        self.projects[project.id] = project
        return project

    def get_project(self, project_id: str) -> Project:
        """Get project by id"""
        return self.projects.get(project_id, None)
    
    
    def remove_project(self, project_id: str):
        """Remove project by id"""
        if project_id in self.projects:
            del self.projects[project_id]


    def get_all_projects(self) -> list:
        """Get all projects"""
        return list(self.projects.values())
    
    def update_project(self, project_id: str, project: Project):
        """Update project by id"""
        if project_id in self.projects:
            self.projects[project_id] = project
