import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data with correct paths
required_downloads = {
    'punkt': 'tokenizers/punkt',
    'punkt_tab': 'tokenizers/punkt_tab', 
    'stopwords': 'corpora/stopwords',
    'wordnet': 'corpora/wordnet'
}

for name, path in required_downloads.items():
    try:
        nltk.data.find(path)
    except LookupError:
        print(f"Downloading {name}...")
        nltk.download(name)

# Initialize tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))


def clean_text(text):
    """
    Cleans and preprocesses a given text string.
    Removes special characters, converts to lowercase,
    removes stopwords, and lemmatizes words.
    """
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs, HTML tags, and special characters
    text = re.sub(r"http\S+|www\S+|<.*?>", "", text)
    text = re.sub(r"[^a-z\s]", "", text)  # keep only alphabets
    
    # Tokenize
    words = nltk.word_tokenize(text)
    
    # Remove stopwords & lemmatize
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    
    # Join back into a single string
    return " ".join(words)
