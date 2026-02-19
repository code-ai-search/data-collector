"""
Tokenization and POS-tagging utilities using NLTK.

Provides:
 - ensure_nltk_resources: download resources if missing
 - sentence_tokenize(text) -> List[str]
 - word_tokenize(sentence) -> List[str]
 - pos_tag_tokens(tokens) -> List[Tuple[str, str]]
 - article_to_sent_tokens_pos(article) -> List[List[Tuple[str,str]]]
"""
from typing import List, Tuple, Dict
import nltk

# NLTK resources we need
_NLTK_RESOURCES = ["punkt", "averaged_perceptron_tagger", "wordnet"]

def ensure_nltk_resources(resources: List[str] = None):
    """Download NLTK resources if they are not already present."""
    resources = resources or _NLTK_RESOURCES
    for r in resources:
        try:
            nltk.data.find(f"tokenizers/{r}") if r == "punkt" else nltk.data.find(f"taggers/{r}")
        except LookupError:
            nltk.download(r)

# Call once on import to be helpful in interactive runs (safe to remove if you prefer manual control)
try:
    ensure_nltk_resources()
except Exception:
    # In environments without internet, downloads may fail; raise when functions actually need the resources
    pass

def sentence_tokenize(text: str) -> List[str]:
    """Return list of sentence strings from text."""
    return nltk.sent_tokenize(text)

def word_tokenize(sentence: str) -> List[str]:
    """Return list of token strings for a sentence."""
    return nltk.word_tokenize(sentence)

def pos_tag_tokens(tokens: List[str]) -> List[Tuple[str, str]]:
    """
    Return list of (token, pos_tag) pairs using NLTK's averaged_perceptron_tagger.
    Example: [('Apple', 'NNP'), ('is', 'VBZ'), ('big', 'JJ')]
    """
    return nltk.pos_tag(tokens)

def article_to_sent_tokens_pos(article: Dict) -> List[List[Tuple[str, str]]]:
    """
    Convert article dict -> list of sentences, each a list of (token, pos) tuples.
    article expected to have 'body' or 'text' key.
    """
    text = article.get("body", article.get("text", ""))
    sents = sentence_tokenize(text)
    tokenized = []
    for s in sents:
        toks = word_tokenize(s)
        toks_pos = pos_tag_tokens(toks)
        tokenized.append(toks_pos)
    return tokenized

# Small helper for interactive sanity check
if __name__ == "__main__":
    sample = "Apple is looking at buying U.K. startup for $1 billion. This is a test."
    print(article_to_sent_tokens_pos({"body": sample}))
