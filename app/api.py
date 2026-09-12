import json,time,uuid
from fastapi import FastAPI
from pydantic import BaseModel
from .agent import ask
from .rag import load_docs

app=FastAPI(title="E-commerce Student Capstone Agent")
LOG="data/requests.jsonl"

class AskRequest(BaseModel):
    query:str
    thread_id:str="api-default"
class AskResponse(BaseModel):
    answer:str; route:str; sources:list[str]; escalation_score:float|None; guardrail:str
class DocumentRequest(BaseModel):
    title:str
    content:str

@app.post("/ask",response_model=AskResponse)
def ask_endpoint(req:AskRequest):
    trace=str(uuid.uuid4()); start=time.perf_counter()
    out=ask(req.query,req.thread_id)
    elapsed=round((time.perf_counter()-start)*1000,2)
    Path=__import__("pathlib").Path
    Path(LOG).parent.mkdir(exist_ok=True)
    with open(LOG,"a",encoding="utf8") as f:
        f.write(json.dumps({"trace_id":trace,"timing_ms":elapsed,"query":__import__("app.guardrails",fromlist=["mask_pii"]).mask_pii(req.query)})+"\n")
    return out

@app.post("/add-document")
def add_document(req:DocumentRequest):
    return {"accepted":True,"title":req.title,"message":"Document accepted for the student project's document workflow. Restart indexing to include it."}
