# embedder_llama.py
import numpy as np
from typing import List
import requests
import random
import logging
from .utils import LLAMA_MODEL, LLMSTUDIO_URL, LLAMA_VECTOR_SIZE

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LlamaEmbedder:
    """
    Genera embeddings usando LLaMA vía LMStudio.
    Compatible con salida estilo OpenAI (data -> embedding).
    """

    def __init__(self, model: str = None):
        self.model = model or LLAMA_MODEL

    def encode(self, texts):
        single = False
        if isinstance(texts, str):
            texts = [texts]
            single = True

        vectors = []
        for text in texts:
            try:
                payload = {
                    "model": self.model,
                    "input": text,
                    "type": "embedding"
                }

                resp = requests.post(
                    f"{LLMSTUDIO_URL}/v1/embeddings",
                    json=payload,
                    timeout=30
                )

                resp.raise_for_status()
                data = resp.json()

                # != AQUI ESTA LO IMPORTANTE ==
                # LM Studio formato:
                # { "data": [ { "embedding": [...]} ] }
                vec = data["data"][0]["embedding"]

                vectors.append(list(map(float, vec)))

            except Exception as e:
                logger.warning(f"Error generando embedding para texto: {e}")
                vectors.append([random.random() for _ in range(LLAMA_VECTOR_SIZE)])

        return vectors[0] if single else vectors