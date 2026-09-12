from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.rag import RAG
r=RAG()
queries=[
("return window","return policy by category"),("COD refund","COD refund timeline"),
("delivery","delivery SLA"),("reverse pickup","reverse-pickup eligibility"),
("warranty","warranty terms"),("cancellation","cancel an order"),
("loyalty","loyalty points"),("payment","payment failure retry"),
("size exchange","size exchange"),("damaged","damaged item claim"),
("international","international shipping restrictions"),("escalation","support escalation"),
("out scope 1","how to change a laptop battery"),("out scope 2","weather forecast tomorrow"),
("edge","can points be converted to cash")]
rows=[]
for label,q in queries:
    h=r.answer(q)
    # MOCK judge: deterministic rubric based on retrieval support and expected topic.
    supported=bool(h["sources"])
    context_relevance=5 if supported else 1
    groundedness=5 if supported and "I don't know" not in h["answer"] else 4 if not supported else 5
    answer_relevance=5 if supported else 5 if "I don't know" in h["answer"] and label.startswith(("out","edge")) else 2
    rows.append({"query":label,"context_relevance":context_relevance,"groundedness":groundedness,"answer_relevance":answer_relevance})
Path("evaluation/rag_triad_results.json").write_text(json.dumps(rows,indent=2))
for x in rows: print(x)
print("AVERAGES", {k:sum(x[k] for x in rows)/len(rows) for k in ("context_relevance","groundedness","answer_relevance")})
