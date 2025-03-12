import Wav2Lip

class AudioProcessor:
    def __init__(self, audio):
        self.audio = audio
        self.video.metadata = {}
        
    def process_audio(self, audio_path):
        """
        Process the input audio file to create mel spectrogram.

        Args:
            audio_path (str): Path to the input audio file

        Returns:
            numpy.ndarray: Mel spectrogram of the audio
        """
        audio = Wav2Lip.audio
        wav = audio.load_wav(audio_path, sr=16000)
        mel = audio.melspectrogram(wav)
        return mel