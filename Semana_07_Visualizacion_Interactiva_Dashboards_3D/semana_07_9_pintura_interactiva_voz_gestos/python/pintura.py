import cv2
import math
import numpy as np
import mediapipe as mp
import speech_recognition as sr
import threading
import queue

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

q = queue.Queue()

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
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

_, img = cap.read()
canvas = np.zeros_like(img) if _ else np.zeros((720, 1280, 3), dtype=np.uint8)

color = (255, 0, 0)
thick = 10
px, py = 0, 0
msg = ""
timer = 0

with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
    running = True
    while cap.isOpened() and running:
        ret, frame = cap.read()
        if not ret: continue

        while not q.empty():
            c = q.get()
            if "rojo" in c: color = (0, 0, 255); msg = "rojo"; timer = 30
            elif "verde" in c: color = (0, 255, 0); msg = "verde"; timer = 30
            elif "azul" in c: color = (255, 0, 0); msg = "azul"; timer = 30
            elif "amarillo" in c: color = (0, 255, 255); msg = "amarillo"; timer = 30
            elif "naranja" in c: color = (0, 165, 255); msg = "naranja"; timer = 30
            elif "morado" in c: color = (128, 0, 128); msg = "morado"; timer = 30
            elif "rosado" in c or "rosa" in c: color = (203, 192, 255); msg = "rosado"; timer = 30
            elif "blanco" in c: color = (255, 255, 255); msg = "blanco"; timer = 30
            elif "celeste" in c or "cian" in c: color = (255, 255, 0); msg = "celeste"; timer = 30
            elif "limpiar" in c or "borrar" in c: canvas = np.zeros_like(frame); msg = "limpio"; timer = 30
            elif "guardar" in c: cv2.imwrite("img.png", canvas); msg = "guardado"; timer = 30
            elif "goma" in c: color = (0, 0, 0); msg = "goma"; timer = 30
            elif "pincel" in c: color = (255, 0, 0); msg = "pincel"; timer = 30
            elif "cerrar" in c or "salir" in c: running = False; break
                
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        if res.multi_hand_landmarks:
            for hand_lm, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
                
                ix = int(hand_lm.landmark[8].x * frame.shape[1])
                iy = int(hand_lm.landmark[8].y * frame.shape[0])
                mx = int(hand_lm.landmark[12].x * frame.shape[1])
                my = int(hand_lm.landmark[12].y * frame.shape[0])
                
                i_up = hand_lm.landmark[8].y < hand_lm.landmark[6].y
                m_up = hand_lm.landmark[12].y < hand_lm.landmark[10].y
                
                # chequear boton cerrar inferior
                if ix < 130 and iy > 650:
                    running = False
                    
                if i_up and m_up:
                    px, py = 0, 0
                    cv2.rectangle(frame, (ix, iy - 25), (mx, my + 25), color, -1)    
                elif i_up:
                    cv2.circle(frame, (ix, iy), 15, color, -1)
                    if px == 0 and py == 0: 
                        px, py = ix, iy
                        
                    if color == (0, 0, 0): # borrando (goma)
                        cv2.line(canvas, (px, py), (ix, iy), color, thick + 40)
                        cv2.circle(frame, (ix, iy), 20, (255, 255, 255), 2)
                    else: 
                        # pintando (pincel)
                        cv2.line(canvas, (px, py), (ix, iy), color, thick)
                    px, py = ix, iy
                else:
                    px, py = 0, 0
                    
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)
        inv = cv2.bitwise_and(frame, frame, mask=mask)
        frame = cv2.bitwise_or(inv, canvas)

        if timer > 0:
            cv2.putText(frame, msg, (10, 50), 1, 2, (0, 255, 255), 2)
            timer -= 1
            
        cv2.circle(frame, (1240, 30), 15, color, -1)
        if color == (0,0,0): cv2.circle(frame, (1240, 30), 15, (255,255,255), 1)

        h_frame = frame.shape[0]
        cv2.rectangle(frame, (10, h_frame - 60), (130, h_frame - 10), (0, 0, 255), -1)
        cv2.putText(frame, "Cerrar", (25, h_frame - 25), 1, 1.5, (255, 255, 255), 2)

        cv2.imshow('paint', frame)
        if cv2.waitKey(1) == 27: break
            
cap.release()
cv2.destroyAllWindows()