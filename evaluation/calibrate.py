from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.rag import RAG
r=RAG()
inside=["What is the return window for footwear?","How long does COD refund take?","What is the delivery SLA?"]
outside=["How do I repair my car engine?","Who won yesterday's football match?"]
for q in inside+outside:
    h=r.retrieve(q,"sentence",1)
    print(("IN " if q in inside else "OUT"),repr(q),round(h[0]["similarity"],4) if h else None)
print("Choose a threshold strictly between the observed in-scope lower cluster and out-of-scope upper cluster, then record the measured values in README.md.")
