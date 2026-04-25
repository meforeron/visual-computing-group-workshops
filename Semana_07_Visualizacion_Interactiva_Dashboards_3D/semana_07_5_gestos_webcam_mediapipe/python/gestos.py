import cv2
import mediapipe as mp
import numpy as np
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

x_obj, y_obj = 320, 240
bg_color = (0, 0, 0)
s_idx = 0
scenes = ["1: Base", "2: Juego"]
score = 0
tx, ty = np.random.randint(100, 500), np.random.randint(100, 400)

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
  while cap.isOpened():
    ret, frame = cap.read()
    if not ret: continue

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(frame_rgb)

    # overlay
    overlay = np.zeros_like(frame, dtype=np.uint8)
    overlay[:] = bg_color
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    dedos = 0
    
    if res.multi_hand_landmarks:
      for hand_lm, h_info in zip(res.multi_hand_landmarks, res.multi_handedness):
        mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
        
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        
        up = []
        is_right = h_info.classification[0].label == 'Right'
        
        # thumb
        if is_right:
            up.append(1 if hand_lm.landmark[tips[0]].x < hand_lm.landmark[pips[0]].x else 0)
        else:
            up.append(1 if hand_lm.landmark[tips[0]].x > hand_lm.landmark[pips[0]].x else 0)
                
        # fingers
        for i in range(1, 5):
            up.append(1 if hand_lm.landmark[tips[i]].y < hand_lm.landmark[pips[i]].y else 0)
        
        dedos = sum(up)
        
        # dist (index, thumb)
        idx_x, idx_y = int(hand_lm.landmark[8].x * frame.shape[1]), int(hand_lm.landmark[8].y * frame.shape[0])
        th_x, th_y = int(hand_lm.landmark[4].x * frame.shape[1]), int(hand_lm.landmark[4].y * frame.shape[0])
        
        d = math.hypot(th_x - idx_x, th_y - idx_y)
        
        cv2.circle(frame, (idx_x, idx_y), 10, (255, 0, 0), -1)
        cv2.circle(frame, (th_x, th_y), 10, (255, 0, 0), -1)
        cv2.line(frame, (idx_x, idx_y), (th_x, th_y), (255, 0, 0), 3)
        
        # pinza
        if d < 40:
            cx, cy = (idx_x + th_x) // 2, (idx_y + th_y) // 2
            x_obj, y_obj = cx, cy
            cv2.circle(frame, (cx, cy), 15, (0, 255, 0), -1)
            
        # change scene
        if dedos == 5:
            if not hasattr(cap, 'wait') or cv2.getTickCount() - cap.wait > cv2.getTickFrequency() * 1.5:
                s_idx = (s_idx + 1) % len(scenes)
                cap.wait = cv2.getTickCount()
                
    # maps
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
            tx, ty = np.random.randint(100, 500), np.random.randint(100, 400)
    
    cv2.imshow('cam', frame)
    if cv2.waitKey(1) == 27: break

cap.release()
cv2.destroyAllWindows()