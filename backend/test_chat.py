import requests
import json

LLMSTUDIO_URL = "http://127.0.0.1:1234/v1/embeddings"   # CAMBIA el puerto si no es 1234



# Cambia el modelo si estás usando otro
MODEL = "text-embedding-nomic-embed-text-v1.5"

def test_embedding(text):
    print("\n=== Probando LM Studio Embeddings ===")
    payload = {
        "model": MODEL,
        "input": text,
        "type": "embedding"
    }

    resp = requests.post(LLMSTUDIO_URL, json=payload)

    print("\nStatus code:", resp.status_code)

    if resp.status_code != 200:
        print("ERROR:", resp.text)
        return

    data = resp.json()

    print("\nRespuesta cruda completa:\n")
    print(json.dumps(data, indent=4)[:3000])  # no saturar la terminal

    try:
        emb = data["data"][0]["embedding"]
        print("\nLongitud del embedding:", len(emb))
        print("Primeros 10 valores:", emb[:10])
    except Exception as e:
        print("\nERROR extrayendo embedding:", e)

if __name__ == "__main__":
    test_embedding("Hola mundo")
