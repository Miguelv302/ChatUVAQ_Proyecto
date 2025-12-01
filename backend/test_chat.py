# admin_upload_cli.py
import requests
import sys
import os

API_URL = "http://localhost:8000/admin/upload_document"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "1921643")  # cambia o exporta en .env

def upload_file(path):
    if not os.path.exists(path):
        print("Archivo no encontrado:", path)
        return

    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "application/octet-stream")}
        try:
            res = requests.post(API_URL, headers=headers, files=files, timeout=120)
            print("Status:", res.status_code)
            print(res.text)
        except Exception as e:
            print("Error al subir archivo:", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python admin_upload_cli.py /ruta/al/archivo.pdf")
        sys.exit(1)
    upload_file(sys.argv[1])
