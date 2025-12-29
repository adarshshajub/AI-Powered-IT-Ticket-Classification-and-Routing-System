import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from ai.utils.nlppreprocess import clean_text
from ai.utils.embeddings import get_embedding


class Command(BaseCommand):
    help = 'Run AI training category'

    def handle(self, *args, **options):
        # Define paths inside handle()
        TRAIN_DATA_PATH = settings.BASE_DIR / "static" / "data"
        TRAIN_DATA_FILE = TRAIN_DATA_PATH / "ai_training_data.csv"
        CATEGORY_MODEL = TRAIN_DATA_PATH / "category_ai.pkl"

        self.stdout.write("Loading dataset...")
        
        # Load dataset
        df = pd.read_csv(TRAIN_DATA_FILE)

        self.stdout.write("Cleaning text...")
        # Clean text
        df["clean_text"] = df["description"].apply(clean_text)

        self.stdout.write("Generating embeddings...")
        # Convert text → embeddings
        X = np.vstack(df["clean_text"].apply(get_embedding).to_list())
        y = df["category"]

        self.stdout.write("Splitting data...")
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.stdout.write("Training model...")
        # Train classifier on embeddings
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y_train)

        self.stdout.write("Evaluating model...")
        # Evaluate
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        self.stdout.write(self.style.SUCCESS(f'Category Model Accuracy: {acc:.4f}'))

        self.stdout.write("Saving model...")
        # Save
        joblib.dump(clf, CATEGORY_MODEL)
        self.stdout.write(self.style.SUCCESS(f'Category model saved to: {CATEGORY_MODEL}'))
