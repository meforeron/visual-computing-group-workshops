import cv2
import mediapipe as mp
import numpy as np
import math
import time
import argparse
import sys
import threading
import platform
from collections import deque

# Import winsound on Windows for auditory feedback
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winsound

class PostureDetector:
    def __init__(self, input_source='webcam', output_path=None, show_window=True):
        self.input_source = input_source
        self.output_path = output_path
        self.show_window = show_window
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # For drawing landmarks
        self.mp_drawing = mp.solutions.drawing_utils
        
        # History for movement tracking (used to detect walking)
        # Store (left_ankle.x, left_ankle.y, right_ankle.x, right_ankle.y)
        self.history_len = 20
        self.ankle_history = deque(maxlen=self.history_len)
        
        # State machine
        self.current_state = "Iniciando"
        self.state_colors = {
            "De pie": (0, 255, 0),        # Green
            "Sentado": (0, 0, 255),       # Red
            "Brazos arriba": (255, 255, 0), # Cyan
            "Caminando": (0, 255, 255),   # Yellow
            "Iniciando": (150, 150, 150),
            "Desconocido": (100, 100, 100)
        }
        
        # State frequencies for beeps
        self.state_beeps = {
            "De pie": (500, 100),       # Frequency (Hz), Duration (ms)
            "Sentado": (400, 200),
            "Brazos arriba": (800, 200),
            "Caminando": (600, 200)
        }
        
        # HUD flash trigger
        self.last_state = "Iniciando"
        self.flash_timer = 0
        self.flash_duration = 10 # Frames to flash UI on transition
        
    def calculate_angle(self, a, b, c):
        """
        Calculate the angle formed by three points: a (end), b (vertex), c (end).
        Points are represented as lists/tuples [x, y].
        Returns the angle in degrees [0, 180].
        """
        a = np.array(a) # End point (e.g., Shoulder)
        b = np.array(b) # Vertex point (e.g., Hip)
        c = np.array(c) # End point (e.g., Knee)
        
        # Vector BA and BC
        ba = a - b
        bc = c - b
        
        # Dot product and magnitudes
        dot_product = np.dot(ba, bc)
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        
        if norm_ba == 0 or norm_bc == 0:
            return 0.0
            
        cosine_angle = dot_product / (norm_ba * norm_bc)
        # Clip value to avoid domain errors in arccos due to precision issues
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)

    def trigger_beep(self, state):
        """Play a beep sound in a separate thread so it doesn't block the video processing."""
        if not IS_WINDOWS or state not in self.state_beeps:
            return
        
        freq, dur = self.state_beeps[state]
        def play():
            try:
                winsound.Beep(freq, dur)
            except Exception as e:
                pass
        
        threading.Thread(target=play, daemon=True).start()

    def classify_posture(self, landmarks, w, h):
        """
        Classifies the posture based on landmarks geometry:
        - Sentado (Sitting)
        - Brazos levantados (Arms Raised)
        - Caminando (Walking)
        - De pie (Standing)
        """
        # Extract coordinates of key joints
        # MediaPipe landmarks are normalized (0 to 1)
        # We also convert them to pixel coordinates for angle/distance calculation
        def get_coords(idx):
            lm = landmarks.landmark[idx]
            return [lm.x, lm.y], [int(lm.x * w), int(lm.y * h)], lm.visibility
            
        # Left and Right Key joints
        nose_norm, nose_px, nose_v = get_coords(self.mp_pose.PoseLandmark.NOSE)
        
        l_shoulder_norm, l_shoulder_px, l_shoulder_v = get_coords(self.mp_pose.PoseLandmark.LEFT_SHOULDER)
        r_shoulder_norm, r_shoulder_px, r_shoulder_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_SHOULDER)
        
        l_elbow_norm, l_elbow_px, l_elbow_v = get_coords(self.mp_pose.PoseLandmark.LEFT_ELBOW)
        r_elbow_norm, r_elbow_px, r_elbow_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_ELBOW)
        
        l_wrist_norm, l_wrist_px, l_wrist_v = get_coords(self.mp_pose.PoseLandmark.LEFT_WRIST)
        r_wrist_norm, r_wrist_px, r_wrist_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_WRIST)
        
        l_hip_norm, l_hip_px, l_hip_v = get_coords(self.mp_pose.PoseLandmark.LEFT_HIP)
        r_hip_norm, r_hip_px, r_hip_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_HIP)
        
        l_knee_norm, l_knee_px, l_knee_v = get_coords(self.mp_pose.PoseLandmark.LEFT_KNEE)
        r_knee_norm, r_knee_px, r_knee_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_KNEE)
        
        l_ankle_norm, l_ankle_px, l_ankle_v = get_coords(self.mp_pose.PoseLandmark.LEFT_ANKLE)
        r_ankle_norm, r_ankle_px, r_ankle_v = get_coords(self.mp_pose.PoseLandmark.RIGHT_ANKLE)
        
        # 1. Calculate main joint angles
        # Hip Angle (Shoulder - Hip - Knee)
        left_hip_angle = self.calculate_angle(l_shoulder_norm, l_hip_norm, l_knee_norm)
        right_hip_angle = self.calculate_angle(r_shoulder_norm, r_hip_norm, r_knee_norm)
        avg_hip_angle = (left_hip_angle + right_hip_angle) / 2.0
        
        # Knee Angle (Hip - Knee - Ankle)
        left_knee_angle = self.calculate_angle(l_hip_norm, l_knee_norm, l_ankle_norm)
        right_knee_angle = self.calculate_angle(r_hip_norm, r_knee_norm, r_ankle_norm)
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2.0
        
        # Track ankle history for walking detection
        self.ankle_history.append((l_ankle_norm[0], l_ankle_norm[1], r_ankle_norm[0], r_ankle_norm[1]))
        
        # Calculate speed/variance of ankle movement
        std_movement = 0.0
        if len(self.ankle_history) >= 5:
            # Calculate standard deviation of horizontal (x) position of ankles to measure stride alternation
            left_xs = [pt[0] for pt in self.ankle_history]
            right_xs = [pt[2] for pt in self.ankle_history]
            std_left = np.std(left_xs)
            std_right = np.std(right_xs)
            std_movement = (std_left + std_right) / 2.0

        # 2. Classification Logic
        # Condition A: Arms Raised (Wrists above nose)
        # Note: In MediaPipe, y is 0 at top, 1 at bottom. So "above" means smaller y-value.
        arms_raised = False
        if l_wrist_v > 0.5 and r_wrist_v > 0.5:
            # Both wrists above nose
            if l_wrist_norm[1] < nose_norm[1] and r_wrist_norm[1] < nose_norm[1]:
                arms_raised = True
                
        # Condition B: Sitting (Hips bent near 90 deg AND knees bent near 90 deg)
        # Usually between 65° and 125° when sitting
        sitting = False
        if 65 < avg_hip_angle < 125 and 65 < avg_knee_angle < 125:
            sitting = True
            
        # Condition C: Walking (Upright posture + active ankle coordinate oscillation)
        walking = False
        # Upright hips and knees (angles > 130 deg)
        upright = avg_hip_angle > 130 and avg_knee_angle > 130
        if upright and std_movement > 0.008:  # Empirical threshold for walking movement
            walking = True
            
        # Determine state
        if arms_raised:
            state = "Brazos arriba"
        elif sitting:
            state = "Sentado"
        elif walking:
            state = "Caminando"
        elif upright:
            state = "De pie"
        else:
            state = "Desconocido"
            
        # Trigger auditory feedback on state change
        if state != self.current_state and state != "Desconocido":
            self.trigger_beep(state)
            self.flash_timer = self.flash_duration
            self.last_state = self.current_state
            self.current_state = state
            
        return {
            "state": self.current_state,
            "angles": {
                "l_hip": left_hip_angle, "r_hip": right_hip_angle, "avg_hip": avg_hip_angle,
                "l_knee": left_knee_angle, "r_knee": right_knee_angle, "avg_knee": avg_knee_angle
            },
            "std_movement": std_movement,
            "joints": {
                "nose": nose_px,
                "l_shoulder": l_shoulder_px, "r_shoulder": r_shoulder_px,
                "l_elbow": l_elbow_px, "r_elbow": r_elbow_px,
                "l_wrist": l_wrist_px, "r_wrist": r_wrist_px,
                "l_hip": l_hip_px, "r_hip": r_hip_px,
                "l_knee": l_knee_px, "r_knee": r_knee_px,
                "l_ankle": l_ankle_px, "r_ankle": r_ankle_px
            }
        }

    def draw_hud(self, frame, analysis, fps):
        """Draws a beautiful high-tech overlay showing status, angles, and detected posture."""
        h, w, _ = frame.shape
        state = analysis["state"]
        color = self.state_colors.get(state, (255, 255, 255))
        
        # State visual feedback flash border
        if self.flash_timer > 0:
            flash_intensity = int(255 * (self.flash_timer / self.flash_duration))
            # Draw a border around the frame
            cv2.rectangle(frame, (0, 0), (w-1, h-1), color, thickness=10)
            self.flash_timer -= 1
            
        # 1. Overlay dashboard container (semi-transparent)
        hud_w, hud_h = 320, 240
        hud_x, hud_y = 20, 20
        
        # Add translucent background panel
        sub_img = frame[hud_y:hud_y+hud_h, hud_x:hud_x+hud_w]
        white_rect = np.zeros(sub_img.shape, dtype=np.uint8)
        white_rect[:] = 20 # Dark background
        res = cv2.addWeighted(sub_img, 0.4, white_rect, 0.6, 0)
        frame[hud_y:hud_y+hud_h, hud_x:hud_x+hud_w] = res
        
        # Dashboard Outline
        cv2.rectangle(frame, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), color, 2)
        
        # Title
        cv2.putText(frame, "HUD POSTURA - MEDIAPIPE", (hud_x + 15, hud_y + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        
        # State label
        cv2.putText(frame, f"ACCION: {state.upper()}", (hud_x + 15, hud_y + 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
                    
        # Angle Info
        hip_ang = analysis["angles"]["avg_hip"]
        knee_ang = analysis["angles"]["avg_knee"]
        std_mov = analysis["std_movement"]
        
        cv2.putText(frame, f"Angulo Cadera: {hip_ang:.1f} deg", (hud_x + 15, hud_y + 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Angulo Rodilla: {knee_ang:.1f} deg", (hud_x + 15, hud_y + 145), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Mov. Tobillo: {std_mov*100:.2f} (std)", (hud_x + 15, hud_y + 180), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
                    
        # FPS and system status
        cv2.putText(frame, f"FPS: {fps:.1f}", (hud_x + 15, hud_y + 215), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        cv2.putText(frame, f"AUDIO: {'WIN_BEEP' if IS_WINDOWS else 'OFF'}", (hud_x + 180, hud_y + 215), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)

    def draw_skeleton(self, frame, analysis):
        """Draws a beautiful custom skeletal network with joints and connecting lines."""
        joints = analysis["joints"]
        state = analysis["state"]
        color = self.state_colors.get(state, (255, 255, 255))
        
        # Connections to draw
        connections = [
            ("l_shoulder", "r_shoulder"),
            ("l_shoulder", "l_hip"), ("r_shoulder", "r_hip"),
            ("l_hip", "r_hip"),
            ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"),
            ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
            ("l_hip", "l_knee"), ("l_knee", "l_ankle"),
            ("r_hip", "r_knee"), ("r_knee", "r_ankle")
        ]
        
        # Draw connection lines with soft glow effect
        for p1_name, p2_name in connections:
            pt1 = joints[p1_name]
            pt2 = joints[p2_name]
            # Verify coordinates are valid and within screen limits
            if pt1[0] > 0 and pt1[1] > 0 and pt2[0] > 0 and pt2[1] > 0:
                # Thin glow outline
                cv2.line(frame, (pt1[0], pt1[1]), (pt2[0], pt2[1]), (255, 255, 255), 4)
                # Primary line
                cv2.line(frame, (pt1[0], pt1[1]), (pt2[0], pt2[1]), color, 2)
                
        # Draw joint nodes
        for joint_name, pt in joints.items():
            if pt[0] > 0 and pt[1] > 0:
                # Head/Nose gets a special node size
                if joint_name == "nose":
                    cv2.circle(frame, (pt[0], pt[1]), 12, (255, 255, 255), -1)
                    cv2.circle(frame, (pt[0], pt[1]), 8, color, -1)
                else:
                    # Joint node
                    cv2.circle(frame, (pt[0], pt[1]), 7, (255, 255, 255), -1)
                    cv2.circle(frame, (pt[0], pt[1]), 5, color, -1)
                    
        # Render angle text next to hip and knee joints
        l_hip = joints["l_hip"]
        r_hip = joints["r_hip"]
        l_knee = joints["l_knee"]
        r_knee = joints["r_knee"]
        
        cv2.putText(frame, f"{analysis['angles']['l_hip']:.0f}deg", (l_hip[0] - 50, l_hip[1] + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{analysis['angles']['r_hip']:.0f}deg", (r_hip[0] + 10, r_hip[1] + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{analysis['angles']['l_knee']:.0f}deg", (l_knee[0] - 50, l_knee[1] + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{analysis['angles']['r_knee']:.0f}deg", (r_knee[0] + 10, r_knee[1] + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)

    def run(self):
        """Main execution loop."""
        # Handle input source
        if self.input_source == 'mock':
            print("[INFO] Iniciando modo SIMULADOR (Mock)...")
            self.run_mock_simulator()
            return
            
        if self.input_source == 'webcam':
            source = 0
            print("[INFO] Abriendo cámara web (0)...")
        else:
            source = self.input_source
            print(f"[INFO] Abriendo archivo de video: {source}...")
            
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"[ERROR] No se pudo abrir la fuente de video: {source}")
            if self.input_source == 'webcam':
                print("[WARNING] Cayendo en modo SIMULADOR (Mock) automáticamente...")
                self.run_mock_simulator()
            return
            
        # Get frame properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        in_fps = cap.get(cv2.CAP_PROP_FPS)
        if in_fps <= 0:
            in_fps = 30.0
            
        print(f"[INFO] Video cargado: {width}x{height} a {in_fps} FPS.")
        
        # Configure VideoWriter if output requested
        out = None
        if self.output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path, fourcc, in_fps, (width, height))
            print(f"[INFO] Guardando video procesado en: {self.output_path}")

        prev_time = time.time()
        fps = 0.0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Compute FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
            prev_time = curr_time
            
            # Mirror the frame horizontally for standard selfie view if webcam
            if self.input_source == 'webcam':
                frame = cv2.flip(frame, 1)
                
            # Process frame with MediaPipe Pose
            # MediaPipe requires RGB images
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                # Classify posture based on detected landmarks
                analysis = self.classify_posture(results.pose_landmarks, width, height)
                
                # Draw visual layers
                self.draw_skeleton(frame, analysis)
                self.draw_hud(frame, analysis, fps)
            else:
                # In case no body detected
                cv2.putText(frame, "BUSCANDO CUERPO...", (50, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Write frame to output video file
            if out:
                out.write(frame)
                
            # Show output if allowed
            if self.show_window:
                cv2.imshow('Taller Postura - MediaPipe Pose', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        cap.release()
        if out:
            out.release()
        cv2.destroyAllWindows()
        print("[INFO] Procesamiento completado.")

    def run_mock_simulator(self):
        """Simulates MediaPipe landmark results programmatically to test visual HUD and classification logic."""
        width, height = 1280, 720
        fps = 30.0
        total_frames = 400
        
        out = None
        if self.output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
            print(f"[INFO] Guardando video simulado en: {self.output_path}")
            
        for frame_idx in range(total_frames):
            # Create a stylized virtual environment background (dark mesh grid)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = 15 # Off-black background
            
            # Draw grid mesh
            for x in range(0, width, 80):
                cv2.line(frame, (x, 0), (x, height), (30, 30, 30), 1)
            for y in range(0, height, 80):
                cv2.line(frame, (0, y), (width, y), (30, 30, 30), 1)
                
            # Generate simulated posture landmarks
            results = self.get_mock_landmarks(frame_idx)
            
            # Classify based on the mock landmarks
            analysis = self.classify_posture(results.pose_landmarks, width, height)
            
            # Draw skeleton and HUD dashboard
            self.draw_skeleton(frame, analysis)
            self.draw_hud(frame, analysis, fps)
            
            # Draw simulation status text
            phase_name = ""
            if frame_idx < 100:
                phase_name = "SIM: De pie (Estatico)"
            elif frame_idx < 200:
                phase_name = "SIM: Sentando (Inclinacion de cadera/rodilla)"
            elif frame_idx < 300:
                phase_name = "SIM: Brazos arriba (Extensión de muñeca)"
            else:
                phase_name = "SIM: Caminando (Alternancia de piernas)"
                
            cv2.putText(frame, f"[MOCK MODE] Frame: {frame_idx}/{total_frames} | {phase_name}", 
                        (width - 520, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA)
            
            if out:
                out.write(frame)
                
            if self.show_window:
                cv2.imshow('Taller Postura - MediaPipe Pose (MOCK)', frame)
                if cv2.waitKey(15) & 0xFF == ord('q'):
                    break
                    
        if out:
            out.release()
        cv2.destroyAllWindows()
        print("[INFO] Simulación completada.")

    def get_mock_landmarks(self, frame_idx):
        """Generates structured skeleton positions for each frame sequence."""
        # Normalized coords base (Standing)
        nose = [0.5, 0.2]
        left_shoulder = [0.45, 0.35]
        right_shoulder = [0.55, 0.35]
        left_elbow = [0.42, 0.48]
        right_elbow = [0.58, 0.48]
        left_wrist = [0.42, 0.6]
        right_wrist = [0.58, 0.6]
        left_hip = [0.47, 0.55]
        right_hip = [0.53, 0.55]
        left_knee = [0.47, 0.72]
        right_knee = [0.53, 0.72]
        left_ankle = [0.47, 0.9]
        right_ankle = [0.53, 0.9]
        
        # State transitions simulation
        # 1. Sitting: bend hips and knees to 90 degrees
        if 100 <= frame_idx < 200:
            # Transition interpolation factor
            t = min(1.0, (frame_idx - 100) / 20.0)
            
            # Hips drop down
            left_hip[1] = 0.55 + 0.13 * t
            right_hip[1] = 0.55 + 0.13 * t
            
            # Knees push forward and slightly down
            left_knee[0] = 0.47 - 0.10 * t
            left_knee[1] = 0.72 - 0.04 * t
            right_knee[0] = 0.53 + 0.10 * t
            right_knee[1] = 0.72 - 0.04 * t
            
            # Ankles move slightly inward but stay at ground height (y=0.9)
            left_ankle[0] = 0.47 - 0.10 * t
            right_ankle[0] = 0.53 + 0.10 * t
            
            # Wrists rest on lap/knees
            left_wrist[0] = left_knee[0]
            left_wrist[1] = left_knee[1] - 0.05
            right_wrist[0] = right_knee[0]
            right_wrist[1] = right_knee[1] - 0.05
            
        # 2. Arms Raised: standing base with wrists above head
        elif 200 <= frame_idx < 300:
            t = min(1.0, (frame_idx - 200) / 20.0)
            
            # Wrists move above nose (y=0.2) to y=0.1
            left_wrist[1] = 0.6 - 0.52 * t
            left_wrist[0] = 0.42 - 0.04 * t
            right_wrist[1] = 0.6 - 0.52 * t
            right_wrist[0] = 0.58 + 0.04 * t
            
            # Elbows bend upwards too
            left_elbow[1] = 0.48 - 0.25 * t
            left_elbow[0] = 0.42 - 0.03 * t
            right_elbow[1] = 0.48 - 0.25 * t
            right_elbow[0] = 0.58 + 0.03 * t
            
        # 3. Walking: standing posture with periodic leg strides
        elif 300 <= frame_idx <= 400:
            phase = (frame_idx - 300) * 0.3
            amp = 0.08
            
            # Ankles alternate left-right in a horizontal sine wave
            left_ankle[0] = 0.47 + amp * math.sin(phase)
            right_ankle[0] = 0.53 - amp * math.sin(phase)
            
            # Knee positions flex slightly to accompany the ankle movement
            left_knee[0] = 0.47 + (amp * 0.4) * math.sin(phase)
            right_knee[0] = 0.53 - (amp * 0.4) * math.sin(phase)
            
            # Arms swing in opposition to legs
            left_wrist[1] = 0.6 + 0.08 * math.sin(phase)
            right_wrist[1] = 0.6 - 0.08 * math.sin(phase)

        # Build Mock Landmarks List
        class MockLandmark:
            def __init__(self, x, y, z=0.0, visibility=0.99):
                self.x = x
                self.y = y
                self.z = z
                self.visibility = visibility
                
        class MockPoseLandmarks:
            def __init__(self, lms):
                self.landmark = lms
                
        class MockPoseResults:
            def __init__(self, lms):
                self.pose_landmarks = lms
                
        # 33 landmarks total
        landmarks_list = [MockLandmark(0.5, 0.5, visibility=0.1) for _ in range(33)]
        
        # Insert key joints (mapped by MediaPipe PoseLandmark index)
        landmarks_list[0] = MockLandmark(*nose)               # Nose (0)
        landmarks_list[11] = MockLandmark(*left_shoulder)     # Left shoulder (11)
        landmarks_list[12] = MockLandmark(*right_shoulder)    # Right shoulder (12)
        landmarks_list[13] = MockLandmark(*left_elbow)        # Left elbow (13)
        landmarks_list[14] = MockLandmark(*right_elbow)       # Right elbow (14)
        landmarks_list[15] = MockLandmark(*left_wrist)        # Left wrist (15)
        landmarks_list[16] = MockLandmark(*right_wrist)       # Right wrist (16)
        landmarks_list[23] = MockLandmark(*left_hip)          # Left hip (23)
        landmarks_list[24] = MockLandmark(*right_hip)         # Right hip (24)
        landmarks_list[25] = MockLandmark(*left_knee)         # Left knee (25)
        landmarks_list[26] = MockLandmark(*right_knee)        # Right knee (26)
        landmarks_list[27] = MockLandmark(*left_ankle)        # Left ankle (27)
        landmarks_list[28] = MockLandmark(*right_ankle)       # Right ankle (28)
        
        return MockPoseResults(MockPoseLandmarks(landmarks_list))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Detección de postura y acciones corporales en tiempo real usando MediaPipe.")
    parser.add_argument('--input', type=str, default='webcam', 
                        help="Fuente de video: 'webcam', 'mock' (simulado) o ruta al archivo de video .mp4")
    parser.add_argument('--output', type=str, default=None, 
                        help="Ruta para guardar el video resultante .mp4")
    parser.add_argument('--headless', action='store_true', 
                        help="Deshabilita cv2.imshow (útil para ejecuciones sin pantalla en servidores o pruebas automatizadas)")
                        
    args = parser.parse_args()
    
    detector = PostureDetector(
        input_source=args.input,
        output_path=args.output,
        show_window=not args.headless
    )
    
    detector.run()
