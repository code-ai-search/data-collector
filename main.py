from scripts import data_loader as dl
from scripts import preprocess as pp

# iterate over the cnn text files
for article in dl.iter_articles():
    tokens = pp.article_to_sent_tokens_pos(article)
    print(tokens[3:5])
