import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from sklearn.multiclass import OneVsRestClassifier
from ai.utils.nlppreprocess import clean_text
from ai.utils.embeddings import get_embedding
import warnings
warnings.filterwarnings('ignore')

class Command(BaseCommand):
    help = 'Run AI training priority'

    def handle(self, *args, **options):
        TRAIN_DATA_PATH = settings.BASE_DIR / "static" / "data"
        TRAIN_DATA_FILE = TRAIN_DATA_PATH / "ai_training_data.csv"
        PRIORITY_MODEL = TRAIN_DATA_PATH / "priority_ai.pkl"

        self.stdout.write("Loading dataset...")
        df = pd.read_csv(TRAIN_DATA_FILE)
        
        # SHOW CLASS IMBALANCE
        self.stdout.write("Priority distribution:")
        print(df['priority'].value_counts())
        print(df['priority'].value_counts(normalize=True) * 100)

        self.stdout.write("Cleaning text...")
        df["clean_text"] = df["description"].apply(clean_text)

        self.stdout.write("Generating embeddings...")
        X = np.vstack(df["clean_text"].apply(get_embedding).to_list())
        y = df["priority"]

        self.stdout.write("Stratified split...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.stdout.write("Training balanced multiclass model...")
        # ✅ FIXED: Use OneVsRestClassifier with liblinear for multiclass
        base_clf = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
            solver='liblinear'  # Works inside OneVsRestClassifier
        )
        clf = OneVsRestClassifier(base_clf)
        
        clf.fit(X_train, y_train)

        self.stdout.write("Evaluating...")
        preds = clf.predict(X_test)
        
        acc = accuracy_score(y_test, preds)
        self.stdout.write(self.style.SUCCESS(f'Accuracy: {acc:.4f}'))
        print("\nDetailed Report:")
        print(classification_report(y_test, preds))
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, preds))

        self.stdout.write("Saving model...")
        joblib.dump(clf, PRIORITY_MODEL)
        self.stdout.write(self.style.SUCCESS(f'Model saved: {PRIORITY_MODEL}'))
