import joblib
from pathlib import Path
from ai.utils.embeddings import get_embedding
from django.conf import settings

AI_MODEL_PATH  = settings.BASE_DIR / "static" / "data"
CATEGORY_MODEL = AI_MODEL_PATH / "category_ai.pkl"
PRIORITY_MODEL = AI_MODEL_PATH / "priority_ai.pkl"

category_model = None
priority_model = None

def load_category_model():
    global category_model
    if category_model is None:
        category_model = joblib.load(CATEGORY_MODEL)
    return category_model

def predict_category(text: str) -> str:
    model = load_category_model()
    embedding = get_embedding(text)
    return model.predict([embedding])[0]

def predict_category_confidence(text: str):
    model = load_category_model()
    embedding = get_embedding(text)
    probs = model.predict_proba([embedding])[0]
    idx = probs.argmax()
    return float(probs[idx])

def load_priority_model():
    global priority_model
    if priority_model is None:
        priority_model = joblib.load(PRIORITY_MODEL)
    return priority_model

def predict_priority(text: str) -> str:
    model = load_priority_model()
    embedding = get_embedding(text)
    return model.predict([embedding])[0]

def predict_priority_confidence(text: str):
    model = load_priority_model()
    embedding = get_embedding(text)
    probs = model.predict_proba([embedding])[0]
    idx = probs.argmax()
    return float(probs[idx])
