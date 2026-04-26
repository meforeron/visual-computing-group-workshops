import cv2
import mediapipe as mp
import speech_recognition as sr
import pygame
import threading
import math
import time
import random
import argparse

# ══════════════════════════════════════════════════════════════
#  ESTADO COMPARTIDO
# ══════════════════════════════════════════════════════════════

class AppState:
    COLORS = {
        "azul":     (100, 149, 237),
        "rojo":     (220,  60,  60),
        "verde":    ( 60, 200, 100),
        "amarillo": (240, 200,  40),
        "morado":   (150,  80, 200),
        "naranja":  (240, 140,  40),
        "blanco":   (220, 220, 220),
        "cyan":     ( 40, 200, 220),
    }
    SHAPES = ["hexagono", "circulo", "cuadrado", "triangulo", "estrella"]

    def __init__(self):
        self._lock        = threading.Lock()
        self.running      = True
        self.gesture      = "none"
        self.fingers_up   = 0
        self.hand_present = False
        self.voice_cmd    = ""
        self.voice_raw    = ""
        self.voice_time   = 0.0
        self.color        = self.COLORS["azul"]
        self.rotating     = False
        self.angle        = 0.0
        self.obj_x        = 400
        self.obj_y        = 300
        self.visible      = True
        self.shape_idx    = 0
        self.action_msg   = "Esperando gesto + comando..."
        self.action_time  = time.time()

    def lock(self):
        return self._lock

    def set_action(self, msg):
        self.action_msg  = msg
        self.action_time = time.time()
        print(f"[ACCION] {msg}")

    def apply_action(self, gesture, command):
        acted = False

        if gesture == "open_hand":
            if command in self.COLORS:
                self.color = self.COLORS[command]
                self.set_action(f"Mano abierta + '{command}' -> color cambiado")
                acted = True
            elif command == "cambiar":
                self.color = random.choice(list(self.COLORS.values()))
                self.set_action("Mano abierta + 'cambiar' -> color aleatorio")
                acted = True
        elif gesture == "two_fingers":
            if command == "mover":
                self.obj_x = random.randint(280, 700)
                self.obj_y = random.randint(150, 450)
                self.set_action("Dos dedos + 'mover' -> reposicionado")
                acted = True
            elif command == "cambiar":
                self.shape_idx = (self.shape_idx + 1) % len(self.SHAPES)
                self.set_action(f"Dos dedos + 'cambiar' -> {self.SHAPES[self.shape_idx]}")
                acted = True
        elif gesture == "fist":
            if command == "rotar":
                self.rotating = not self.rotating
                self.set_action(f"Puno + 'rotar' -> {'ON' if self.rotating else 'OFF'}")
                acted = True
        elif gesture == "point":
            if command in ("mostrar", "ocultar"):
                self.visible = not self.visible
                self.set_action(f"Senalar + '{command}' -> {'visible' if self.visible else 'oculto'}")
                acted = True
            elif command in self.COLORS:
                self.color = self.COLORS[command]
                self.set_action(f"Senalar + '{command}' -> color aplicado")
                acted = True

        # if not acted:
        #     if command == "rotar":
        #         self.rotating = not self.rotating
        #         self.set_action(f"'{command}' -> {'ON' if self.rotating else 'OFF'}")
        #     elif command in ("mostrar", "ocultar"):
        #         self.visible = not self.visible
        #         self.set_action(f"'{command}' -> {'visible' if self.visible else 'oculto'}")
        #     elif command == "mover":
        #         self.obj_x = random.randint(280, 700)
        #         self.obj_y = random.randint(150, 450)
        #         self.set_action("'mover' -> reposicionado")
        #     elif command == "cambiar":
        #         self.color = random.choice(list(self.COLORS.values()))
        #         self.set_action("'cambiar' -> color aleatorio")
        #     elif command in self.COLORS:
        #         self.color = self.COLORS[command]
        #         self.set_action(f"'{command}' -> color cambiado")



# Mapa teclas → comandos (funciona en AMBAS ventanas)
KEY_COMMANDS_PYGAME = {
    pygame.K_a: "azul",    pygame.K_r: "rojo",    pygame.K_v: "verde",
    pygame.K_m: "morado",  pygame.K_n: "naranja",  pygame.K_b: "blanco",
    pygame.K_y: "amarillo", pygame.K_c: "cambiar", pygame.K_w: "mover",
    pygame.K_t: "rotar",   pygame.K_o: "ocultar",  pygame.K_s: "mostrar",
}
KEY_COMMANDS_CV2 = {
    ord('a'): "azul",    ord('r'): "rojo",     ord('v'): "verde",
    ord('m'): "morado",  ord('n'): "naranja",   ord('b'): "blanco",
    ord('y'): "amarillo", ord('c'): "cambiar",  ord('w'): "mover",
    ord('t'): "rotar",   ord('o'): "ocultar",   ord('s'): "mostrar",
}

CAM_W, CAM_H = 640, 480


# ══════════════════════════════════════════════════════════════
#  DETECTOR DE GESTOS
# ══════════════════════════════════════════════════════════════

class GestureDetector:
    def __init__(self, state, source):
        self.state    = state
        self.source   = source
        mp_h          = mp.solutions.hands
        self.mp_hands = mp_h
        self.mp_draw  = mp.solutions.drawing_utils
        self.hands    = mp_h.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )

    def count_fingers(self, lm):
        """
        Deteccion robusta por DISTANCIA DESDE LA MUNECA.
        Funciona con la mano en CUALQUIER orientacion
        (vertical, horizontal, inclinada).

        Para cada dedo:  si la punta esta mas lejos de la
        muneca que el nudillo MCP -> dedo extendido.

        Pulgar: compara tip(4) vs CMC(1) desde muneca(0).
        """
        wx = lm[0].x
        wy = lm[0].y

        def dist(a, b):
            return math.sqrt((lm[a].x - lm[b].x)**2 + (lm[a].y - lm[b].y)**2)

        fingers = 0

        # ── Pulgar: tip(4) vs CMC(1) ──────────────────────────
        # Usamos un umbral un poco mayor (1.15) para evitar falsos positivos
        if dist(4, 0) > dist(1, 0) * 2.2:
            fingers += 1

        # ── Indice, medio, anular, menique: tip vs MCP ────────
        # tips:  8, 12, 16, 20
        # mcps:  5,  9, 13, 17
        for tip_idx, mcp_idx in [(8,5), (12,9), (16,13), (20,17)]:
            if dist(tip_idx, 0) > dist(mcp_idx, 0)*1.4:
                fingers += 1

        return fingers

    @staticmethod
    def fingers_to_gesture(n):
        return {0: "fist", 1: "point", 2: "two_fingers", 5: "open_hand"}.get(n, "other")

    def run(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            print(f"[GESTOS] No se pudo abrir: {self.source}")
            return

        is_video = isinstance(self.source, str)
        print(f"[GESTOS] Fuente: {'video archivo' if is_video else 'webcam'}")
        if is_video:
            print("[GESTOS] Modo VIDEO -> teclas en ventana CAMARA o PYGAME:")
            print("  A=azul R=rojo V=verde M=morado N=naranja B=blanco Y=amarillo")
            print("  C=cambiar  W=mover  T=rotar  O=ocultar  S=mostrar  Q=salir")

        while self.state.running:
            ok, frame = cap.read()
            if not ok:
                if is_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            # Redimensionar y reflejar
            frame  = cv2.resize(frame, (CAM_W, CAM_H))
            frame  = cv2.flip(frame, 1)
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            with self.state.lock():
                if result.multi_hand_landmarks:
                    lm      = result.multi_hand_landmarks[0].landmark
                    n       = self.count_fingers(lm)
                    gesture = self.fingers_to_gesture(n)

                    self.state.hand_present = True
                    self.state.fingers_up   = n
                    self.state.gesture      = gesture

                    self.mp_draw.draw_landmarks(
                        frame, result.multi_hand_landmarks[0],
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(0, 255, 120), thickness=2, circle_radius=4),
                        self.mp_draw.DrawingSpec(color=(255, 200, 0), thickness=2),
                    )
                    cv2.putText(frame, f"Gesto: {gesture}  ({n} dedos)",
                                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 120), 2)
                    if self.state.rotating and gesture != "fist":
                        self.rotating = False
                else:
                    self.state.hand_present = False
                    self.state.gesture      = "none"
                    self.state.fingers_up   = 0
                    cv2.putText(frame, "Sin mano detectada",
                                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (80, 80, 80), 2)

            if is_video:
                cv2.putText(frame,
                            "Teclas (aqui o en Pygame): A=azul R=rojo C=cambiar W=mover T=rotar O=ocultar",
                            (6, CAM_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 220, 60), 1)

            cv2.imshow("Camara - Deteccion de Gestos  [Q=salir]", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.state.running = False
                break
            elif key in KEY_COMMANDS_CV2:
                cmd = KEY_COMMANDS_CV2[key]
                with self.state.lock():
                    self.state.voice_raw  = f"[tecla {chr(key).upper()} en camara]"
                    self.state.voice_cmd  = cmd
                    self.state.voice_time = time.time()
                    self.state.apply_action(self.state.gesture, cmd)

        cap.release()
        cv2.destroyAllWindows()
        print("[GESTOS] Hilo terminado.")


# ══════════════════════════════════════════════════════════════
#  ESCUCHADOR DE VOZ
# ══════════════════════════════════════════════════════════════

VALID_COMMANDS = {
    "azul", "rojo", "verde", "amarillo", "morado", "naranja", "blanco", "cyan",
    "cambiar", "mover", "rotar", "mostrar", "ocultar",
}

class VoiceListener:
    def __init__(self, state):
        self.state = state
        self.r     = sr.Recognizer()
        self.r.energy_threshold       = 300
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold        = 0.5

    def run(self):
        print("[VOZ] Iniciando microfono...")
        try:
            with sr.Microphone() as src:
                print("[VOZ] Calibrando ruido ambiente (2 s)...")
                self.r.adjust_for_ambient_noise(src, duration=2)
        except (OSError, AttributeError) as e:
            # OSError = no hay microfono
            # AttributeError = PyAudio no instalado
            print(f"[VOZ] Microfono no disponible: {e}")
            print("[VOZ] -> Usa TECLAS en la ventana Pygame o Camara como alternativa.")
            return

        print(f"[VOZ] Listo. Comandos: {', '.join(sorted(VALID_COMMANDS))}")

        while self.state.running:
            try:
                with sr.Microphone() as src:
                    audio = self.r.listen(src, timeout=4, phrase_time_limit=3)
                text = self.r.recognize_google(audio, language="es-ES").lower().strip()
                print(f"[VOZ] Escuche: '{text}'")
                cmd = next((c for c in VALID_COMMANDS if c in text), "")
                with self.state.lock():
                    self.state.voice_raw  = text
                    self.state.voice_cmd  = cmd
                    self.state.voice_time = time.time()
                    if cmd:
                        self.state.apply_action(self.state.gesture, cmd)
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[VOZ] Error Google: {e}")
                time.sleep(3)
            except (OSError, AttributeError):
                print("[VOZ] Microfono desconectado. Usa teclas.")
                return
            except Exception as e:
                if self.state.running:
                    print(f"[VOZ] Error: {e}")

        print("[VOZ] Hilo terminado.")


# ══════════════════════════════════════════════════════════════
#  ESCENA VISUAL (Pygame)
# ══════════════════════════════════════════════════════════════

def draw_shape(surface, shape, cx, cy, size, color, angle):
    def poly(n, r, ox, oy, off=0):
        return [(ox + r*math.cos(math.radians(off + i*360/n)),
                 oy + r*math.sin(math.radians(off + i*360/n))) for i in range(n)]
    W = (255, 255, 255)
    ix, iy = int(cx), int(cy)
    if shape == "circulo":
        pygame.draw.circle(surface, color, (ix, iy), size)
        pygame.draw.circle(surface, W, (ix, iy), size, 3)
    elif shape == "hexagono":
        pts = poly(6, size, cx, cy, angle)
        pygame.draw.polygon(surface, color, pts); pygame.draw.polygon(surface, W, pts, 3)
    elif shape == "cuadrado":
        pts = poly(4, size, cx, cy, angle+45)
        pygame.draw.polygon(surface, color, pts); pygame.draw.polygon(surface, W, pts, 3)
    elif shape == "triangulo":
        pts = poly(3, size, cx, cy, angle-90)
        pygame.draw.polygon(surface, color, pts); pygame.draw.polygon(surface, W, pts, 3)
    elif shape == "estrella":
        pts = [(cx + (size if i%2==0 else size//2)*math.cos(math.radians(angle-90+i*36)),
                cy + (size if i%2==0 else size//2)*math.sin(math.radians(angle-90+i*36)))
               for i in range(10)]
        pygame.draw.polygon(surface, color, pts); pygame.draw.polygon(surface, W, pts, 3)


def draw_glow(surface, cx, cy, color, base_size):
    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    r, g, b = color
    for radius in range(base_size + 50, base_size, -10):
        alpha = max(0, int(35 * (1 - (radius - base_size) / 50)))
        pygame.draw.circle(glow, (r, g, b, alpha), (int(cx), int(cy)), radius)
    surface.blit(glow, (0, 0))


def draw_hud(surface, state, font_sm, font_md, W, H):
    now = time.time()
    panel = pygame.Surface((240, H), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 150))
    surface.blit(panel, (0, 0))
    y = 14

    def txt(text, font, color=(190, 190, 190)):
        nonlocal y
        s = font.render(text, True, color)
        surface.blit(s, (12, y))
        y += s.get_height() + 5

    HDR = (130, 210, 255); OK = (100, 255, 130); DIM = (110, 110, 130)

    txt("=== ESTADO ===", font_md, HDR)
    hc = OK if state.hand_present else DIM
    txt(f"Gesto  : {state.gesture}", font_sm, hc)
    txt(f"Dedos  : {state.fingers_up}", font_sm, hc)
    txt(f"Mano   : {'detectada' if state.hand_present else 'no detectada'}", font_sm, hc)
    y += 4
    txt("=== ENTRADA ===", font_md, HDR)
    cc = OK if now - state.voice_time < 2.5 else DIM
    txt(f"Cmd    : {state.voice_cmd or '-'}", font_sm, cc)
    raw = (state.voice_raw[-22:] if len(state.voice_raw) > 22 else state.voice_raw) or "-"
    txt(f"Input  : {raw}", font_sm, DIM)
    y += 4
    txt("=== ESCENA ===", font_md, HDR)
    txt(f"Forma  : {AppState.SHAPES[state.shape_idx]}", font_sm)
    r, g, b = state.color
    txt(f"Color  : ({r},{g},{b})", font_sm)
    txt(f"Rotar  : {'ON' if state.rotating else 'OFF'}", font_sm)
    txt(f"Visible: {'SI' if state.visible else 'NO'}", font_sm)

    help_lines = [
        "-- TECLAS AQUI O CAMARA --",
        "A=azul  R=rojo  V=verde",
        "M=morado N=naranja B=blanco",
        "Y=amarillo  C=cambiar",
        "W=mover  T=rotar",
        "O=ocultar  S=mostrar",
        "-- PYGAME EXTRA --",
        "Mayus+R = reset",
        "Q = salir",
        "-- GESTOS + VOZ/TECLA --",
        "5d+color -> color",
        "2d+mover -> mover",
        "0d+rotar -> rotar",
        "1d+ocultar -> ocultar",
    ]
    hy = H - len(help_lines)*16 - 8
    for line in help_lines:
        s = font_sm.render(line, True, (140, 140, 160))
        surface.blit(s, (12, hy))
        hy += 16

    elapsed = now - state.action_time
    if elapsed < 3.5:
        cv_val = int(255 * min(1.0, (3.5 - elapsed) / 0.5))
        ms = font_md.render(state.action_msg, True, (cv_val, int(cv_val*0.94), 80))
        surface.blit(ms, (W//2 - ms.get_width()//2, H - 44))


def run_scene(state):
    pygame.init()
    W, H   = 820, 620
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Interfaz Multimodal - Voz & Gestos | Teclas: A=azul C=cambiar W=mover T=rotar O=ocultar")
    clock  = pygame.time.Clock()
    font_sm = pygame.font.SysFont("monospace", 13)
    font_md = pygame.font.SysFont("monospace", 15, bold=True)
    SHAPE_SIZE = 85
    BG   = (16, 18, 30)
    GRID = (26, 28, 46)

    print("[ESCENA] Ventana Pygame lista.")
    print("[ESCENA] Teclas aqui: A=azul R=rojo V=verde C=cambiar W=mover T=rotar O=ocultar")

    while state.running:
        dt = clock.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                state.running = False

            elif ev.type == pygame.KEYDOWN:
                k = ev.key

                # Salir con Q
                if k == pygame.K_q:
                    state.running = False

                # Reset con Shift+R
                elif k == pygame.K_r and (ev.mod & pygame.KMOD_SHIFT):
                    with state.lock():
                        state.color     = AppState.COLORS["azul"]
                        state.rotating  = False
                        state.angle     = 0.0
                        state.obj_x     = W//2 + 40
                        state.obj_y     = H//2
                        state.visible   = True
                        state.shape_idx = 0
                        state.set_action("Reset completo")

                # Comandos con teclas (sin Shift)
                elif k in KEY_COMMANDS_PYGAME and not (ev.mod & pygame.KMOD_SHIFT):
                    cmd = KEY_COMMANDS_PYGAME[k]
                    with state.lock():
                        state.voice_raw  = f"[tecla {pygame.key.name(k).upper()} en Pygame]"
                        state.voice_cmd  = cmd
                        state.voice_time = time.time()
                        state.apply_action(state.gesture, cmd)

        with state.lock():
            if state.rotating:
                state.angle = (state.angle + 55*dt) % 360
            color   = state.color
            angle   = state.angle
            ox, oy  = state.obj_x, state.obj_y
            visible = state.visible
            shape   = AppState.SHAPES[state.shape_idx]

        screen.fill(BG)
        for gx in range(0, W, 40):
            pygame.draw.line(screen, GRID, (gx, 0), (gx, H))
        for gy in range(0, H, 40):
            pygame.draw.line(screen, GRID, (0, gy), (W, gy))

        if visible:
            draw_glow(screen, ox, oy, color, SHAPE_SIZE)
            draw_shape(screen, shape, ox, oy, SHAPE_SIZE, color, angle)

        with state.lock():
            draw_hud(screen, state, font_sm, font_md, W, H)

        with state.lock():
            hp = state.hand_present
            gt = state.gesture
        dc = (80, 255, 120) if hp else (70, 70, 90)
        pygame.draw.circle(screen, dc, (W-22, 22), 11)
        gs = font_sm.render(gt, True, dc)
        screen.blit(gs, (W - 35 - gs.get_width(), 15))

        pygame.display.flip()

    pygame.quit()
    print("[ESCENA] Ventana cerrada.")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Interfaz Multimodal: Voz + Gestos")
    parser.add_argument("--video", type=str, default=None)
    parser.add_argument("--cam",   type=int, default=0)
    args   = parser.parse_args()
    source = args.video 
    if args.video:
        source = args.video
    else:
        source = "http://192.168.81.27:8080/video"
    print(f"[MAIN] Fuente: {source}")

    state = AppState()

    threading.Thread(target=GestureDetector(state, source).run,
                     name="GestureThread", daemon=True).start()
    threading.Thread(target=VoiceListener(state).run,
                     name="VoiceThread", daemon=True).start()

    run_scene(state)
    state.running = False
    print("[MAIN] Cerrado.")

if __name__ == "__main__":
    main()

