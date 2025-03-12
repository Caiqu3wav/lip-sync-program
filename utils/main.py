from moviepy import VideoFileClip

def get_video_duration(video_path):
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"Erro ao obter duração do vídeo: {e}")
        return None