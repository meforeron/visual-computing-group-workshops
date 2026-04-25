import cv2
import mediapipe as mp
import numpy as np
import speech_recognition as sr
import threading
import queue

mp_d = mp.solutions.drawing_utils
mp_h = mp.solutions.hands

q = queue.Queue()

# thread voz
def listen():
    rec = sr.Recognizer()
    mic = sr.Microphone()
    with mic as s: rec.adjust_for_ambient_noise(s)
    
    while True:
        try:
            with mic as s: audio = rec.listen(s, phrase_time_limit=3)
            txt = rec.recognize_google(audio, language="es-ES").lower()
            q.put(txt)
        except: pass

threading.Thread(target=listen, daemon=True).start()

cap = cv2.VideoCapture(0)
_, img = cap.read()
canvas = np.zeros_like(img) if _ else np.zeros((480, 640, 3), dtype=np.uint8)

color = (255, 0, 0)
thick = 10
px, py = 0, 0
msg = ""
timer = 0

with mp_h.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
  while cap.isOpened():
    ret, frame = cap.read()
    if not ret: continue

    # cmds
    while not q.empty():
        c = q.get()
        if "rojo" in c: color = (0, 0, 255); msg = "rojo"; timer = 30
        elif "verde" in c: color = (0, 255, 0); msg = "verde"; timer = 30
        elif "azul" in c: color = (255, 0, 0); msg = "azul"; timer = 30
        elif "limpiar" in c or "borrar" in c: canvas = np.zeros_like(frame); msg = "limpio"; timer = 30
        elif "guardar" in c: cv2.imwrite("img.png", canvas); msg = "guardado"; timer = 30
        elif "goma" in c: color = (0, 0, 0); msg = "goma"; timer = 30
        elif "pincel" in c: color = (255, 0, 0); msg = "pincel"; timer = 30
            
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        for lm, info in zip(res.multi_hand_landmarks, res.multi_handedness):
            mp_d.draw_landmarks(frame, lm, mp_h.HAND_CONNECTIONS)
            
            ix, iy = int(lm.landmark[8].x * frame.shape[1]), int(lm.landmark[8].y * frame.shape[0])
            mx, my = int(lm.landmark[12].x * frame.shape[1]), int(lm.landmark[12].y * frame.shape[0])
            
            i_up = lm.landmark[8].y < lm.landmark[6].y
            m_up = lm.landmark[12].y < lm.landmark[10].y
            
            # draw / hover
            if i_up and m_up:
                px, py = 0, 0
                cv2.rectangle(frame, (ix, iy - 25), (mx, my + 25), color, -1)    
            elif i_up:
                cv2.circle(frame, (ix, iy), 15, color, -1)
                if px == 0 and py == 0: px, py = ix, iy
                    
                if color == (0, 0, 0): # goma
                    cv2.line(canvas, (px, py), (ix, iy), color, thick + 40)
                    cv2.circle(frame, (ix, iy), 20, (255, 255, 255), 2)
                else: 
                    # pincel
                    cv2.line(canvas, (px, py), (ix, iy), color, thick)
                px, py = ix, iy
            else:
                px, py = 0, 0
                
    # merge
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)
    inv = cv2.bitwise_and(frame, frame, mask=mask)
    frame = cv2.bitwise_or(inv, canvas)

    # ui
    if timer > 0:
        cv2.putText(frame, msg, (10, 50), 1, 2, (0, 255, 255), 2)
        timer -= 1
        
    cv2.circle(frame, (600, 30), 15, color, -1)
    if color == (0,0,0): cv2.circle(frame, (600, 30), 15, (255,255,255), 1)

    cv2.imshow('paint', frame)
    if cv2.waitKey(1) == 27: break
        
cap.release()
cv2.destroyAllWindows()