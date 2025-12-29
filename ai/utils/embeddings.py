from sentence_transformers import SentenceTransformer
import numpy as np

# Load once (singleton)
_model = None

def load_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def get_embedding(text: str) -> np.ndarray:
    model = load_embedding_model()
    return model.encode(text, normalize_embeddings=True)