"""
Classical feature-based NER using sklearn-crfsuite.

This version expects sentences as lists of (token, pos) tuples, e.g.:
  sent = [('Apple','NNP'), ('is','VBZ'), ('big','JJ')]

It includes features that use the POS tag as well as token forms.
"""
from typing import List, Tuple
import sklearn_crfsuite


TokenPos = Tuple[str, str]  # (token, pos)
SentTP = List[TokenPos]


def word2features(sent: SentTP, i: int) -> dict:
    """
    sent: list of (token, pos)
    Return dict of features for token i.
    """
    token, pos = sent[i]
    features = {
        "bias": 1.0,
        "token.lower()": token.lower(),
        "token[-3:]": token[-3:],
        "token[-2:]": token[-2:],
        "token.isupper()": token.isupper(),
        "token.istitle()": token.istitle(),
        "token.isdigit()": token.isdigit(),
        "pos": pos,
    }
    # previous token
    if i > 0:
        token1, pos1 = sent[i - 1]
        features.update(
            {
                "-1:token.lower()": token1.lower(),
                "-1:pos": pos1,
            }
        )
    else:
        features["BOS"] = True
    # next token
    if i < len(sent) - 1:
        token1, pos1 = sent[i + 1]
        features.update({"+1:token.lower()": token1.lower(), "+1:pos": pos1})
    else:
        features["EOS"] = True
    return features


def sent_to_features(sent: SentTP) -> List[dict]:
    return [word2features(sent, i) for i in range(len(sent))]


def prepare_crf_data(sents: List[SentTP], labels: List[List[str]]):
    """
    sents: list of sentences, each sentence is list of (token,pos)
    labels: list of BIO label lists aligned with tokens for each sentence
    Returns X, y suitable for sklearn-crfsuite
    """
    X = [sent_to_features(s) for s in sents]
    y = labels
    return X, y


class CRFNER:
    def __init__(self, **crf_kwargs):
        self.model = sklearn_crfsuite.CRF(
            algorithm="lbfgs",
            c1=0.1,
            c2=0.1,
            max_iterations=100,
            all_possible_transitions=True,
            **crf_kwargs,
        )

    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path):
        import joblib
        joblib.dump(self.model, path)

    def load(self, path):
        import joblib
        self.model = joblib.load(path)
