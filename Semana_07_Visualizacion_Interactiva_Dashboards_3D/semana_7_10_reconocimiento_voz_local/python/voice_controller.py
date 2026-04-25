import time
from pythonosc.udp_client import SimpleUDPClient
import speech_recognition as sr


OSC_IP = "127.0.0.1"
OSC_PORT = 12000


COMMAND_MAP = {
    "rojo": {"color": [255, 70, 70], "spin": 0, "running": 1},
    "azul": {"color": [70, 120, 255], "spin": 0, "running": 1},
    "verde": {"color": [70, 220, 120], "spin": 0, "running": 1},
    "girar": {"spin": 1},
    "detener": {"running": 0, "spin": 0},
    "iniciar": {"running": 1},
}


def send_visual_state(osc_client: SimpleUDPClient, state: dict) -> None:
    """Send visual state values to Processing through OSC."""
    if "color" in state:
        r, g, b = state["color"]
        osc_client.send_message("/color", [r, g, b])
    if "spin" in state:
        osc_client.send_message("/spin", int(state["spin"]))
    if "running" in state:
        osc_client.send_message("/running", int(state["running"]))


def parse_command(text: str) -> dict:
    """
    Return the state payload associated with the first matching command word.
    """
    lowered = text.lower()
    for key, payload in COMMAND_MAP.items():
        if key in lowered:
            return payload
    return {}


def recognize_speech_offline(recognizer: sr.Recognizer, mic: sr.Microphone) -> str:
    """
    Capture and recognize Spanish speech using the offline PocketSphinx engine.
    """
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        print("Escuchando comando...")
        audio = recognizer.listen(source, phrase_time_limit=3)

    try:
        return recognizer.recognize_sphinx(audio, language="es-ES")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as exc:
        print(f"Error de motor de reconocimiento: {exc}")
        return ""


def main() -> None:
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

    print(f"Enviando OSC a {OSC_IP}:{OSC_PORT}")
    print("Comandos: rojo, azul, verde, girar, iniciar, detener")
    print("Presiona Ctrl + C para salir.")

    while True:
        try:
            text = recognize_speech_offline(recognizer, mic)
            if not text:
                print("No se entendio el comando.")
                continue

            print(f"Reconocido: {text}")
            payload = parse_command(text)
            if not payload:
                print("Comando fuera del diccionario.")
                continue

            send_visual_state(osc_client, payload)
            print(f"OSC enviado: {payload}")
            time.sleep(0.2)

        except KeyboardInterrupt:
            print("\nFinalizado por usuario.")
            break


if __name__ == "__main__":
    main()
