import argparse
import json
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--dir", default="./cnn-lite-articles", help="directory containing the json files. \
  Only files with .json extension will be processed")
parser.add_argument("--logfile", default="json-processing.log", help="directory containing the json files.")
parser.add_argument("--workflow", choices=["title-change"], default="title-change", help="directory containing the json files.")

if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s', filename=args.logfile, encoding='utf-8', level=logging.DEBUG)
    logger.debug('This message should go to the log file')
    p = Path(args.dir)
    for x in p.iterdir():
        if x.suffix == '.json':
            with open(x, 'r') as fh:
                data = json.load(fh)
                if args.workflow == "title-change":
                    # TODO: factor out to function
                    if "previous_title" in data.keys():
                        print(f"title: {data['title']}")
                        print(f"previous title: {data['previous_title']}")
                else:
                    print(f"Should never get here...")
