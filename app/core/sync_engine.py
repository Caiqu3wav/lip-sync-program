import os
import cv2
import numpy as np
import torch
from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox
import sys
import traceback
from pathlib import Path
from app.core.audio_processor import AudioProcessor
from app.core.video_analyzer import VideoAnalyser

# Import necessary modules for Wav2Lip
from Wav2Lip.models.wav2lip import Wav2Lip as Wav2LipModel

class LipSyncEngine:
    def __init__(self, model_path='wav2lip_gan.pth', low_memory_mode=False):
        """
        Initialize the Lip Sync Engine with Wav2Lip model.
        
        Args:
            model_path (str): Path to the pre-trained Wav2Lip model
            low_memory_mode (bool): Enable optimizations for low memory systems
        """ 
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.low_memory_mode = low_memory_mode
        print(f"Using device: {self.device}")
        print(f"Low memory mode: {'Enabled' if low_memory_mode else 'Disabled'}")

        # Set torch memory optimization if using CPU or low memory mode
        if self.device.type == 'cpu' or low_memory_mode:
            print("Optimizing for low memory usage")
            # Lower precision for CPU calculation
            torch.set_num_threads(4)  # Limit number of threads
            torch.set_grad_enabled(False)  # Make sure gradients are disabled
        
        self.max_resolution = 480 if self.low_memory_mode else 720

        self.video_analyser = VideoAnalyser(device=self.device, low_memory_mode=self.low_memory_mode, max_resolution=self.max_resolution)
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, model_path)
        print(f"Looking for model at: {model_path}")

        # Load Wav2lip model
        try:
            # Import here to avoid issues if the module is not found
            self.model = Wav2LipModel()
            
            if os.path.exists(model_path):
                print(f"Found model file at {model_path}")
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # Print checkpoint keys for debugging
                print(f"Checkpoint keys: {checkpoint.keys()}")
                
                # Check if the checkpoint contains a state_dict key
                if 'state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['state_dict'])
                else:
                    # Try loading directly (in case it's just the state_dict)
                    self.model.load_state_dict(checkpoint)
                    
                self.model.to(self.device)
                self.model.eval()
                print("Model loaded successfully!")
            else:
                print(f"WARNING: Model file not found at {model_path}")
                print(f"You will need to place the Wav2Lip model at this location")
        except Exception as e:
            print(f"Error loading Wav2Lip model: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_lip_sync(self, video_path, audio_path, output_path=None, cartoon_mode=False, batch_process=True):
        """
        Generate lip-synced video by combining video frames with audio.

        Args:
            video_path (str): Path to the input video file
            audio_path (str): Path to the input audio file
            output_path (str, optional): Path to save the output video
            cartoon_mode (bool): Whether to use cartoon-specific processing
            batch_process (bool): Whether to process in batches for memory efficiency

        Returns:
            str: Path to the generated video
        """
        if output_path is None:
            base_name = os.path.splitext(video_path)[0]
            output_path = f"{base_name}_lip_synced.mp4"

        try:
            # Determine processing parameters based on system capabilities
            frame_skip = 2 if self.device.type == 'cpu' and self.low_memory_mode else 1
            
            # Step 1: Extract video frames and get video properties
            print(f"Extracting video frames (max resolution: {self.max_resolution}, frame skip: {frame_skip})...")
            frames, fps, (original_w, original_h) = self.video_analyser.extract_frames(
                video_path, 
                frame_skip=frame_skip,
            )
            
            # Adjust fps if frames were skipped
            effective_fps = fps / frame_skip
            
            # Step 2: Process audio to mel spectrogram
            print("Processing audio...")
            mel_spectrogram = AudioProcessor.process_audio(audio_path=audio_path)
            
            # Step 3: Detect faces in frames
            print("Detecting faces...")
            if cartoon_mode:
                # Skip face detection entirely for cartoons
                h, w = frames[0].shape[:2]
                
                # For an elephant, we want a wider face region that captures the trunk area too
                # Adjust these values based on where the mouth/trunk is in your specific cartoon
                x1, y1 = int(w*0.25), int(h*0.3)  # Top-left corner
                x2, y2 = int(w*0.75), int(h*0.8)  # Bottom-right corner
                
                # Create a consistent face region for all frames
                face_regions = [[x1, y1, x2, y2]] * len(frames)
                print(f"Using predefined face region for cartoon: {[x1, y1, x2, y2]}")
            else:
                # Original face detection code for human faces
                print("Detecting faces...")
                face_regions = self.video_analyser.detect_faces(frames)
            
            # Check if any faces were detected
            if all(region is None for region in face_regions):
                print("No faces detected in any frame. Attempting with manual face region...")
                # Define a default face region (centered, 60% of frame)
                h, w = frames[0].shape[:2]
                x1, y1 = int(w*0.2), int(h*0.2)
                x2, y2 = int(w*0.8), int(h*0.8)
                default_region = [x1, y1, x2, y2]
                face_regions = [default_region] * len(frames)
                print(f"Using manual face region: {default_region}")
            
            # Step 4: Apply lip sync to each frame
            print("Applying lip sync...")

            # Process in batches and write directly for better memory management
            if batch_process:
                # Threshold is lower for low memory mode
                batch_threshold = 200 if self.low_memory_mode else 500
                if len(frames) > batch_threshold:
                    print(f"Processing in batches (threshold: {batch_threshold} frames)")
                    
                    # Create temporary output without audio for direct writing
                    temp_video_path = output_path + "_temp.mp4"
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    
                    # Use the processing resolution, not the original resolution
                    process_h, process_w = frames[0].shape[:2]
                    out = cv2.VideoWriter(temp_video_path, fourcc, effective_fps, (process_w, process_h))
                    
                    # Process in batches
                    # Smaller batch size for low memory mode
                    batch_size = 50 if self.low_memory_mode else 100
                    
                    for i in range(0, len(frames), batch_size):
                        print(f"Processing batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
                        
                        batch_frames = frames[i:i+batch_size]
                        batch_regions = face_regions[i:i+batch_size]
                        
                        for j, (frame, face_region) in enumerate(zip(batch_frames, batch_regions)):
                            global_idx = i + j  # Global frame index for mel spectrogram lookup
                            
                            if face_region is None:
                                # If no face detected, use original frame
                                out.write(frame)
                                continue
                            
                            # Extract face ROI
                            x1, y1, x2, y2 = [int(b) for b in face_region[0:4]]
                            
                            # Ensure coordinates are valid
                            h, w = frame.shape[:2]
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(w, x2), min(h, y2)
                            
                            # Skip this frame if the region is too small
                            if x2 - x1 < 10 or y2 - y1 < 10:
                                out.write(frame)
                                continue
                                
                            face_img = frame[y1:y2, x1:x2]
                            
                            # Resize to model input size
                            face_img = cv2.resize(face_img, (96, 96))

                            # Convert to grayscale (1 channel)
                            face_img_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                            face_tensor = torch.FloatTensor(face_img_gray).unsqueeze(0)
                            print(f"Face tensor shape before conversion: {face_tensor.shape}")

                            # Convert 1-channel to 6-channel by duplicating
                            face_tensor = face_tensor.repeat(1, 6, 1, 1)
                            print(f"Face tensor shape after conversion: {face_tensor.shape}")

                            face_tensor = face_tensor.to(self.device)

                            # Get corresponding mel segment
                            mel_idx = int(global_idx / len(frames) * len(mel_spectrogram))
                            mel_window = mel_spectrogram[max(0, mel_idx-5):mel_idx+5]
                            if len(mel_window) < 10:  # Handle edge case
                                mel_window = np.pad(mel_window, ((0, 10 - len(mel_window)), (0, 0)), 'edge')
                            mel_tensor = torch.FloatTensor(mel_window).unsqueeze(0).to(self.device)
                            print(f"Mel tensor shape: {mel_tensor.shape}")

                            
                            # Generate lip-synced face
                            with torch.no_grad():
                                try:
                                    # Use proper model call based on signature
                                    synced_face = self.model(mel_tensor, face_tensor)
                                    print("Using proper model call based on signature")
                                    
                                    # Get output from tensor
                                    synced_face = synced_face.cpu().numpy().transpose(0, 2, 3, 1)[0]
                                    print("Getting output from tensor")
                                except Exception as e:
                                    print(f"Error generating lip-sync for frame {global_idx}: {e}")
                                    out.write(frame)
                                    break
                                
                            # Resize back to original face size
                            synced_face = cv2.resize(synced_face, (x2-x1, y2-y1))
                            
                            # For cartoon mode, use special blending function
                            if cartoon_mode:
                                result_frame = self.blend_cartoon_face(frame, synced_face, x1, y1, x2, y2)
                            else:
                                # Regular blending for non-cartoon faces
                                result_frame = frame.copy()
                                result_frame[y1:y2, x1:x2] = synced_face
                            
                            # Write frame directly to video
                            out.write(result_frame)
                            
                            if global_idx % 100 == 0:
                                print(f"Processed {global_idx}/{len(frames)} frames")
                        
                        # Clear memory after each batch
                        del batch_frames
                        del batch_regions
                        import gc
                        gc.collect()
                        
                    out.release()
                    
                    # Step 5: Add audio to the video
                    print("Adding audio to video...")
                    final_output = self.add_audio_to_video(temp_video_path, audio_path, output_path)
                    
                    # Remove temp file
                    try:
                        os.remove(temp_video_path)
                    except:
                        print(f"Could not remove temporary file {temp_video_path}")
                    
                    print(f"Lip-sync completed! Output saved to: {final_output}")
                    return final_output
                    
            # Original non-batched processing (for shorter videos)
            synced_frames = []
            
            for i, (frame, face_region) in enumerate(zip(frames, face_regions)):
                if face_region is None:
                    # If no face detected, use original frame
                    synced_frames.append(frame)
                    continue
                
                # Extract face ROI
                x1, y1, x2, y2 = [int(b) for b in face_region[0:4]]
                
                # Ensure coordinates are valid
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                # Skip this frame if the region is too small
                if x2 - x1 < 10 or y2 - y1 < 10:
                    synced_frames.append(frame)
                    continue
                    
                face_img = frame[y1:y2, x1:x2]
                
                # Resize to model input size
                face_img = cv2.resize(face_img, (96, 96))

                face_img_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                
                # Convert to tensor
                face_tensor = torch.FloatTensor(face_img_gray).unsqueeze(0).unsqueeze(0).to(self.device)
                print(f"Face tensor shape before conversion: {face_tensor.shape}")

                face_tensor = face_tensor.repeat(1, 6, 1, 1)
                print(f"Face tensor shape after conversion: {face_tensor.shape}")

                # Get corresponding mel segment
                mel_idx = int(i / len(frames) * len(mel_spectrogram))
                mel_window = mel_spectrogram[max(0, mel_idx-5):mel_idx+5]
                if len(mel_window) < 10:  # Handle edge case
                    mel_window = np.pad(mel_window, ((0, 10 - len(mel_window)), (0, 0)), 'edge')
                mel_tensor = torch.FloatTensor(mel_window).unsqueeze(0).to(self.device)
                
                # Generate lip-synced face
                with torch.no_grad():
                    try:
                        # Use model forward pass without extra parameters
                        synced_face = self.model(face_tensor, mel_tensor)
                        synced_face = synced_face.cpu().numpy().transpose(0, 2, 3, 1)[0]  # (C,H,W) -> (H,W,C)
                    except Exception as e:
                        print(f"Error generating lip-sync for frame index {i}: {e}")
                        synced_frames.append(frame)
                        continue
                    
                # Resize back to original face size
                synced_face = cv2.resize(synced_face, (x2-x1, y2-y1))
                
                # For cartoon mode, use special blending function
                if cartoon_mode:
                    result_frame = self.blend_cartoon_face(frame, synced_face, x1, y1, x2, y2)
                else:
                    # Regular blending for non-cartoon faces
                    result_frame = frame.copy()
                    result_frame[y1:y2, x1:x2] = synced_face
                
                synced_frames.append(result_frame)
                
                if i % 100 == 0:
                    print(f"Processed {i}/{len(frames)} frames")

                # For very low memory, periodically write frames and clear memory
                if self.low_memory_mode and len(synced_frames) > 500:
                    if i == 500:  # First batch - create the writer
                        temp_video_path = output_path + "_temp.mp4"
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        process_h, process_w = synced_frames[0].shape[:2]
                        out = cv2.VideoWriter(temp_video_path, fourcc, effective_fps, (process_w, process_h))
                    
                    # Write frames in batches
                    for frame in synced_frames:
                        out.write(frame)
                    
                    # Clear memory
                    synced_frames = []
                    import gc
                    gc.collect()

            # If using incremental writing in low memory mode, finalize video
            if self.low_memory_mode and not synced_frames:
                out.release()
                final_output = self.add_audio_to_video(temp_video_path, audio_path, output_path)
                try:
                    os.remove(temp_video_path)
                except:
                    print(f"Could not remove temporary file {temp_video_path}")
                
                print(f"Lip-sync completed! Output saved to: {final_output}")
                return final_output
            
            # Otherwise, save all frames at once
            print("Saving video...")
            self.save_video(output_path, synced_frames, effective_fps, (original_w, original_h), audio_path)
            
            print(f"Lip-sync completed! Output saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error during lip-sync: {e}")
            traceback.print_exc()
            raise

def main():
    # Create PyQt application
    app = QApplication(sys.argv)
    
    # Detect system capabilities
    import psutil
    memory_gb = psutil.virtual_memory().total / (1024 ** 3)
    cpu_count = psutil.cpu_count(logical=False)
    has_gpu = torch.cuda.is_available()
    
    print(f"System info: RAM: {memory_gb:.1f}GB, CPU cores: {cpu_count}, GPU: {'Yes' if has_gpu else 'No'}")
    
    # Auto-detect low memory mode
    low_memory_mode = memory_gb < 16 and not has_gpu
    
    # Create the lip sync engine
    try:
        sync_engine = LipSyncEngine(low_memory_mode=low_memory_mode)
        
        # Ask for video file
        video_path = QFileDialog.getOpenFileName(None, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")[0]
        if not video_path:
            print("No video file selected. Exiting.")
            return
            
        # Ask for audio file
        audio_path = QFileDialog.getOpenFileName(None, "Select Audio File", "", "Audio Files (*.wav *.mp3)")[0]
        if not audio_path:
            print("No audio file selected. Exiting.")
            return
            
        # Diretório padrão dentro de "Documents"
        default_output_dir = Path.home() / "Documents" / "VideoSubtitleAutomation" / "output"

        # Criar a pasta caso não exista
        default_output_dir.mkdir(parents=True, exist_ok=True)

        # Diálogo para salvar o arquivo dentro da pasta padrão
        output_path = QFileDialog.getSaveFileName(
            None, 
            "Save Output Video", 
            str(default_output_dir / "output.mp4"),  # Caminho padrão para salvar
            "Video Files (*.mp4)"
        )[0]
        
        # Ask if this is for a cartoon
        cartoon_mode = QMessageBox.question(None, "Cartoon Mode", 
                                          "Is this for a cartoon character?",
                                          QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
        
        if cartoon_mode:
            print("Using cartoon mode for better lip-sync with animated characters.")
        
        # Generate lip sync
        sync_engine.generate_lip_sync(video_path, audio_path, output_path, cartoon_mode=cartoon_mode)
        
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()