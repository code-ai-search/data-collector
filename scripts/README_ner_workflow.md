# NER experiment skeleton

Overview:
- data: put cnn-lite json files under data/cnn_lite/
- scripts/
  - data_loader.py: find and yield article dicts
  - preprocess.py: tokenization utilities
  - models/: CRF, HF, LLM wrappers
  - evaluate/: seqeval evaluation

Quick start:
1. Install dependencies (see suggestions).
2. Update DATA_DIR path in scripts/data_loader.py to point to your articles.
3. Implement tokens<->char alignment in utils/align.py.
4. Run a smoke test: python run_experiments.py --data-dir data/cnn_lite
5. Add any gold annotation conversion (if you have gold) and run evaluate/eval_seq.py
