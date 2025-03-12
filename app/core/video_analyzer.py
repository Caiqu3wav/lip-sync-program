import os
import cv2
import numpy as np
import Wav2Lip
from Wav2Lip.face_detection import FaceAlignment, LandmarksType

class VideoAnalyser:
    def __init__(self, device, max_resolution, low_memory_mode=False):
        self.device = device
        self.low_memory_mode = low_memory_mode
        self.max_resolution = max_resolution

    def extract_frames(self, video_path, frame_skip=1):
        """
        Extract frames from a video file.

        Args:
            video_path (str): Path to the input video file
            frame_skip (int): Process every Nth frame (1=all frames, 2=every other frame)

        Returns:
            tuple: (frames, fps, original_dimensions)
        """
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        
        original_w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        scale = 1.0
        if original_h > self.max_resolution:
            scale = self.max_resolution / original_h
            new_w = int(original_w * scale)
            new_h = self.max_resolution
            print(f"Downscaling video from {original_w}x{original_h} to {new_w}x{new_h} for processing")
        else:
            new_w, new_h = original_w, original_h

        frames = []
        frame_count = 0
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Apply frame_skip (can be adjusted for low-end systems)
        effective_fps = fps / frame_skip
        print(f"Processing at effective {effective_fps:.1f} FPS (skipping every {frame_skip} frames)")
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            # Only process every Nth frame if skipping
            if frame_count % frame_skip == 0:
                # Resize if needed
                if scale < 1.0:
                    frame = cv2.resize(frame, (new_w, new_h))
                
                frames.append(frame)
                
                # Show progress
                if len(frames) % 100 == 0:
                    print(f"Extracted {len(frames)} frames out of {total_frames//frame_skip} (estimated)")
            
            frame_count += 1
            
            # For low memory, periodically clear unnecessary variables
            if self.low_memory_mode and frame_count % 1000 == 0:
                import gc
                gc.collect()
        
        video.release()
        
        if not frames:
            raise ValueError(f"No frames could be extracted from {video_path}")
        
        return frames, fps, (original_w, original_h)
    
    def preprocess_cartoon_frame(self, frame):
        """
        Preprocess a frame for cartoon effect.

        Args:
            frame (numpy.ndarray): Input frame

        Returns:
            numpy.ndarray: Preprocessed frame
        """
        enhanced = frame.copy()

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Equalize histogram for better contrast
        equalized = cv2.equalizeHist(gray)

        # Convert back to BGR for consistent processing
        enhanced = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)

        # Apply slight sharpening to enhance edges
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)

        return enhanced
    
    def detect_faces(self, frames, cartoon_mode=True):
        """
        Detect faces in all video frames.

        Args:
            frames (list): List of video frames
            cartoon_mode (bool): Use lower thresholds for cartoon faces

        Returns:
            list: List of detected face regions
        """
        detector = FaceAlignment(LandmarksType._2D, flip_input=False, device=self.device)
        
        # Lower threshold for cartoon detection to catch more features
        if cartoon_mode and hasattr(detector.face_detector, 'det_thresh'):
            original_threshold = detector.face_detector.det_thresh
            detector.face_detector.det_thresh = 0.1
            print("Using lower detection threshold for cartoon faces")

        # Process in small batches to save memory
        batch_size = 8 if self.low_memory_mode else 16
        face_regions = []

        for i in range(0, len(frames), batch_size):
            print(f"Detecting faces in frames {i} to {min(i+batch_size, len(frames)-1)}")
            batch_frames = frames[i:i+batch_size]
            predictions = []
            
            for frame in batch_frames:
                try:
                    # Fixed method call for face detection - use the correct method
                    if hasattr(detector, 'get_detections'):
                        prediction = detector.get_detections(frame)
                    elif hasattr(detector.face_detector, 'detect_from_image'):
                        prediction = detector.face_detector.detect_from_image(frame)
                    else:
                        # Fallback - try to detect directly (some versions have different API)
                        prediction = detector.detect_faces(frame)
                    
                    if len(prediction) == 0:
                        # No face detected
                        if face_regions:
                            # Use previous face if available
                            predictions.append(face_regions[-1])
                        else:
                            predictions.append(None)
                    else:
                        # Use the face with largest bounding box
                        max_area = 0
                        max_pred = None
                        for pred in prediction:
                            # Handle different prediction formats
                            if isinstance(pred, np.ndarray) and pred.shape[0] >= 4:
                                x1, y1, x2, y2 = pred[0:4]
                            elif isinstance(pred, (list, tuple)) and len(pred) >= 4:
                                x1, y1, x2, y2 = pred[0:4]
                            else:
                                continue
                                
                            area = (x2 - x1) * (y2 - y1)
                            if area > max_area:
                                max_area = area
                                max_pred = pred
                        predictions.append(max_pred)
                except Exception as e:
                    print(f"Error in face detection: {e}")
                    predictions.append(None)
            
            face_regions.extend(predictions)
            
            # For low memory mode, clear memory periodically
            if self.low_memory_mode:
                del batch_frames
                import gc
                gc.collect()

        # Reset detector threshold
        if cartoon_mode and hasattr(detector.face_detector, 'det_thresh'):
            detector.face_detector.det_thresh = original_threshold
        
        return face_regions
    
    def blend_cartoon_face(self, frame, synced_face, x1, y1, x2, y2):
        """
        Blend the synced face back into the cartoon frame with smooth transitions.
        
        Args:
            frame (numpy.ndarray): Original video frame
            synced_face (numpy.ndarray): Synced face image
            x1, y1, x2, y2 (int): Face region coordinates
            
        Returns:
            numpy.ndarray: Blended frame
        """
        # Create an elliptical mask for smooth transition
        mask = np.zeros((y2-y1, x2-x1), dtype=np.float32)
        center_x, center_y = int((x2-x1)/2), int((y2-y1)/2)
        radius_x, radius_y = int((x2-x1)/2.5), int((y2-y1)/2.5)
        
        cv2.ellipse(mask, 
                   (center_x, center_y), 
                   (radius_x, radius_y), 
                   0, 0, 360, 1, -1)
        
        # Apply gaussian blur to the mask for smoother edges
        mask = cv2.GaussianBlur(mask, (19, 19), 0)
        
        # Expand mask to 3 channels
        mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        
        # Blend the faces using the mask
        result_frame = frame.copy()
        roi = result_frame[y1:y2, x1:x2]
        result_frame[y1:y2, x1:x2] = synced_face * mask + roi * (1 - mask)
        
        return result_frame
    
    def add_audio_to_video(self, video_path, audio_path, output_path):
        """
        Add audio to a video file using ffmpeg.
        
        Args:
            video_path (str): Path to the input video file
            audio_path (str): Path to the input audio file
            output_path (str): Path to save the output video
            
        Returns:
            str: Path to the output video
        """
        try:
            # Check if ffmpeg is available
            import subprocess
            try:
                subprocess.check_output(['ffmpeg', '-version'])
                print("ffmpeg found, using external process")
            except:
                print("ffmpeg not found in PATH, video will be without audio")
                os.rename(video_path, output_path)
                return output_path
                
            command = [
                'ffmpeg',
                '-i', video_path,   # Input video
                '-i', audio_path,   # Input audio
                '-c:v', 'copy',     # Copy video stream
                '-c:a', 'aac',      # Encode audio as AAC
                '-shortest',        # End when shortest input ends
                '-y',               # Overwrite output
                output_path
            ]
            
            print(f"Running command: {' '.join(command)}")
            subprocess.call(command)
            
            # Check if the output was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Successfully added audio to video: {output_path}")
                return output_path
            else:
                print("Failed to add audio, using video without audio")
                os.rename(video_path, output_path)
                return output_path
                
        except Exception as e:
            print(f"Error adding audio: {e}")
            print(f"Using video without audio")
            os.rename(video_path, output_path)
            return output_path

    def save_video(self, output_path, frames, fps, dimensions=None, audio_path=None):
        """
        Save the generated lip-synced frames as a video with audio.

        Args:
            output_path (str): Path to save the video
            frames (list): List of processed frames
            fps (float): Frame rate of the video
            dimensions (tuple): Width and height of the output video
            audio_path (str): Path to the audio file to merge with video
        """
        if not frames:
            print("No frames to save!")
            return
            
        # Create a temporary video file without audio
        temp_video_path = output_path + "_temp.mp4"
        
        # Get dimensions from first frame if not provided
        if dimensions is None:
            height, width = frames[0].shape[:2]
        else:
            width, height = dimensions
            
            # If we have different processed dimensions vs original
            if frames and (frames[0].shape[1], frames[0].shape[0]) != (width, height):
                print(f"Resizing output from {frames[0].shape[1]}x{frames[0].shape[0]} to {width}x{height}")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
        
        # Write frames to video
        for i, frame in enumerate(frames):
            # Show progress for large videos
            if i % 100 == 0 and len(frames) > 500:
                print(f"Writing frame {i}/{len(frames)} to video")
                
            # Ensure frame is the right format
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            # Ensure frame has the right dimensions
            if frame.shape[:2] != (height, width):
                frame = cv2.resize(frame, (width, height))
                
            # Ensure frame has 3 channels (RGB)
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                
            out.write(frame)
        
        out.release()
        print(f"Video saved to {temp_video_path}")
        
        # Combine video with audio
        if audio_path:
            self.add_audio_to_video(temp_video_path, audio_path, output_path)
            
            # Remove temporary file
            try:
                os.remove(temp_video_path)
            except Exception as e:
                print(f"Could not remove temporary file: {e}")
        else:
            os.rename(temp_video_path, output_path)
    
if __name__ == "__main__":
    video_analyser = VideoAnalyser("videos/video.mp4")
    print(video_analyser.analyse())