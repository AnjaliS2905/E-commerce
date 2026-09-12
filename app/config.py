import os
MOCK_LLM = os.getenv("MOCK_LLM","1") == "1"
TOP_K = int(os.getenv("TOP_K","3"))
# Empirically calibrated in this project after running evaluation/calibrate.py.
# The script rewrites the reported value if the local embedding model changes.
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD","0.42"))
