import Wav2Lip
import Wav2Lip.audio

class AudioProcessor:
    @staticmethod 
    def process_audio(audio_path):
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