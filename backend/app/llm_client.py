# llm_client.py
import requests

LLM_URL = "http://127.0.0.1:1234/v1/chat/completions"

def llm_completion(prompt: str, context: str = ""):
    full_prompt = f"""
Responde basándote estrictamente en el contexto.
Si el contexto no contiene información, responde "No tengo información para responder eso."

Contexto:
{context}

Pregunta:
{prompt}
"""

    resp = requests.post(LLM_URL, json={
        "model": "llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.1
    })
    return resp.json()["choices"][0]["message"]["content"]
