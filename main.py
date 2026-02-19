import json

from nltk import word_tokenize, pos_tag, ne_chunk, sent_tokenize

from scripts import data_loader as dl
from scripts import preprocess as pp
from models import ner_crf


def process_ner(file_path):
    with open(file_path, 'r') as file:
        raw_text = file.read()
    print("raw text")
    article = json.loads(raw_text)
    # 1. Split text into sentences
    sentences = sent_tokenize(article['text'])
    for sentence in sentences:
        # 2. Tokenize and POS tag each sentence
        tokens = word_tokenize(sentence)
        tagged_tokens = pos_tag(tokens)
        # 3. Apply NER chunker
        # Use binary=True if you only want to find entities without classifying them
        ner_tree = ne_chunk(tagged_tokens, binary=False)
        print(f"NER_TREE: {ner_tree!r}")
        # 4. Extract entities from the resulting tree
        for chunk in ner_tree:
            print(chunk)
            if hasattr(chunk, 'label'):
                entity_name = ' '.join(c[0] for c in chunk)
                entity_type = chunk.label()
                print(f"Entity: {entity_name} | Type: {entity_type}")
        input("press any key for next sentence>")

### some misc usage examples...
# example usage:
process_ner('cnn-lite-articles/fe08f9e4225bf227332a4302f0c4648664702080845e2dd543e07cf359a9448b.json')

# iterate over the articles and generate the crf features for each word
X = []
for article in dl.iter_articles():
    tokens = pp.article_to_sent_tokens_pos(article)
    n = len(tokens)
    for i in range(n):
        X.append([ner_crf.word2features(tokens[i], j) for j in range(len(tokens[i]))])

# now length is 3233 so we want that many labels
len(X)



#crf_ner_model = ner_crf.CRFNER()
#crf_ner_model.fit(X_train=X, y_train=y)
