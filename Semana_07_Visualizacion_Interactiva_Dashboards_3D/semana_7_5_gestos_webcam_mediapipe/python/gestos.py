import cv2
import math
import numpy as np
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

x_obj, y_obj = 640, 360
bg_color = (0, 0, 0)
s_idx = 0
scenes = ["1: Base", "2: Juego"]
score = 0
tx, ty = np.random.randint(200, 1080), np.random.randint(150, 550)
last_scene_change_time = 0

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    running = True
    while cap.isOpened() and running:
        ret, frame = cap.read()
        if not ret: continue

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(frame_rgb)

        overlay = np.zeros_like(frame, dtype=np.uint8)
        overlay[:] = bg_color
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        dedos = 0
        
        if res.multi_hand_landmarks:
            for hand_lm, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
                
                tips = [4, 8, 12, 16, 20]
                pips = [3, 6, 10, 14, 18]
                up = []
                
                is_right = hand_info.classification[0].label == 'Right'
                
                # comprobamos el pulgar dependiendo de la mano
                if is_right:
                    up.append(1 if hand_lm.landmark[tips[0]].x < hand_lm.landmark[pips[0]].x else 0)
                else:
                    up.append(1 if hand_lm.landmark[tips[0]].x > hand_lm.landmark[pips[0]].x else 0)
                        
                for i in range(1, 5):
                    up.append(1 if hand_lm.landmark[tips[i]].y < hand_lm.landmark[pips[i]].y else 0)
                
                dedos = sum(up)
                
                ix = int(hand_lm.landmark[8].x * frame.shape[1])
                iy = int(hand_lm.landmark[8].y * frame.shape[0])
                tx_finger = int(hand_lm.landmark[4].x * frame.shape[1])
                ty_finger = int(hand_lm.landmark[4].y * frame.shape[0])
                
                # chequear boton cerrar inferior
                if ix < 130 and iy > 650:
                    running = False
                    
                d = math.hypot(tx_finger - ix, ty_finger - iy)
                
                cv2.circle(frame, (ix, iy), 10, (255, 0, 0), -1)
                cv2.circle(frame, (tx_finger, ty_finger), 10, (255, 0, 0), -1)
                cv2.line(frame, (ix, iy), (tx_finger, ty_finger), (255, 0, 0), 3)
                
                # logica pinza
                if d < 40:
                    cx = (ix + tx_finger) // 2
                    cy = (iy + ty_finger) // 2
                    x_obj, y_obj = cx, cy
                    cv2.circle(frame, (cx, cy), 15, (0, 255, 0), -1)
                    
                # cambio de estado si abre mano
                if dedos == 5:
                    current_time = cv2.getTickCount()
                    if last_scene_change_time == 0 or (current_time - last_scene_change_time) > cv2.getTickFrequency() * 1.5:
                        s_idx = (s_idx + 1) % len(scenes)
                        last_scene_change_time = current_time
                        
        colores = {0:(0,0,0), 1:(200,0,0), 2:(0,200,0), 3:(0,0,200), 4:(0,200,200), 5:(200,0,200)}
        bg_color = colores.get(dedos, (0,0,0))
        
        cv2.putText(frame, scenes[s_idx], (20, 40), 1, 2, (255, 255, 255), 2)
        cv2.putText(frame, str(dedos), (20, 80), 1, 2, (255, 255, 255), 2)
        
        if s_idx == 0:
            cv2.rectangle(frame, (x_obj - 30, y_obj - 30), (x_obj + 30, y_obj + 30), (0, 255, 255), -1)
        elif s_idx == 1:
            cv2.rectangle(frame, (x_obj - 30, y_obj - 30), (x_obj + 30, y_obj + 30), (0, 255, 255), -1)
            cv2.circle(frame, (tx, ty), 20, (0, 0, 255), -1)
            cv2.putText(frame, str(score), (20, 120), 1, 2, (255, 255, 255), 2)
            
            if math.hypot(tx - x_obj, ty - y_obj) < 50:
                score += 1
                tx, ty = np.random.randint(200, 1080), np.random.randint(150, 550)
                
        h_frame = frame.shape[0]
        cv2.rectangle(frame, (10, h_frame - 60), (130, h_frame - 10), (0, 0, 255), -1)
        cv2.putText(frame, "Cerrar", (25, h_frame - 25), 1, 1.5, (255, 255, 255), 2)
        
        cv2.imshow('cam', frame)
        if cv2.waitKey(1) == 27: break

cap.release()
cv2.destroyAllWindows()