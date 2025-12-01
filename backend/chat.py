# chat_cli.py
import requests
import sys

API_URL = "http://localhost:8000/api/chat"

def main():
    print("=== CLI Chat con UVAQ (escribe 'salir' para terminar) ===")
    while True:
        msg = input("Tú: ").strip()
        if not msg:
            continue
        if msg.lower() in ("salir", "exit", "quit"):
            print("Adiós.")
            sys.exit(0)

        try:
            res = requests.post(API_URL, json={"message": msg}, timeout=30)
            if res.status_code != 200:
                print(f"[ERROR {res.status_code}]: {res.text}")
                continue
            data = res.json()
            print("Bot:", data.get("message") or data.get("response") or "(sin respuesta)")
        except Exception as e:
            print("Error conectando al servidor:", e)

if __name__ == "__main__":
    main()
