from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.rag import RAG
rag=RAG()
CASES=[
("return window by category","01_return_window"),
("COD refund timeline","02_cod_refund"),
("delivery SLA","03_delivery_sla"),
("reverse pickup eligibility","04_reverse_pickup"),
("electronics warranty","05_warranty"),
("cancel an order","06_cancellation"),
("redeem loyalty points","07_loyalty_points"),
("payment failed retry","08_payment_retry"),
("size exchange","09_size_exchange"),
("damaged item claim","10_damaged_item"),
("international shipping restrictions","11_international_shipping"),
("support escalation matrix","12_escalation_matrix")]
def score(strategy,q,gold):
    hits=rag.retrieve(q,strategy,3)
    got=list(dict.fromkeys(x["doc"] for x in hits))
    rel=[gold]
    tp=len(set(got)&set(rel))
    p=tp/3
    r=tp/1
    return got,p,r
rows=[]
for q,gold in CASES[:5]:
    for st in ("fixed","sentence"):
        got,p,r=score(st,q,gold); rows.append({"query":q,"strategy":st,"retrieved":got,"precision_at_3":p,"recall_at_3":r,
            "arithmetic":f"{int(p*3)}/3={p:.3f}; {int(r*1)}/1={r:.3f}"})
Path("evaluation/rag_results.json").write_text(json.dumps(rows,indent=2))
for x in rows: print(x)
