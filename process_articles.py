import argparse
import json
import logging

from pathlib import Path

from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--dir", default="./cnn-lite-articles", help="directory containing the json files. \
  Only files with .json extension will be processed")
parser.add_argument("--logfile", default="json-processing.log", help="directory containing the json files.")
parser.add_argument("--workflow", choices=["title-change", "extract-content"], default="title-change", help="directory containing the json files.")
parser.add_argument("--outputfile", help="filepath to put the processed output. Note this will overwrite the file if present.")

#NOTE: the sentences that start with these entries include an actual sentence so we strip them
#      rather than exclude the sentences outright.
EXCLUDE_SENTENCES = ["Source:", "See Full Web Article"]

if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s', filename=args.logfile, encoding='utf-8', level=logging.DEBUG)
    logger.debug('This message should go to the log file')
    p = Path(args.dir)
    out_fh = None
    if args.outputfile:
        out_fh = open(args.outputfile, 'w')
    for x in p.iterdir():
        if x.suffix == '.json':
            with open(x, 'r') as fh:
                data = json.load(fh)
                if args.workflow == "title-change":
                    # TODO: factor out to function
                    if "previous_title" in data.keys():
                        if out_fh:
                            out_fh.write(data['title']+"\n")
                            out_fh.write(data['previous_title']+"\n")
                        else:
                            print(f"title: {data['title']}")
                            print(f"previous title: {data['previous_title']}")
                elif args.workflow == "extract-content":
                    # TODO: factor out to a function
                    sentences = sent_tokenize(data["text"])
                    for sentence in sentences:
                        if out_fh:
                            for i in range(len(EXCLUDE_SENTENCES)):
                                if sentence.startswith(EXCLUDE_SENTENCES[i]):
                                   break
                            else:
                                if not sentence.endswith("\n"):
                                    out_fh.write(sentence+"\n")
                                else:
                                    # TODO: strip any "\n" if >1 of these characters
                                    out_fh.write(sentence)
                        else:
                            print(sentence, "\n")
                else:
                    print(f"Should never get here...")
