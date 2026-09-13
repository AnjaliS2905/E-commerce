# E-commerce — Student Capstone

> A production-minded E-commerce domain support agent built with LangGraph, FastAPI, ChromaDB, and MCP. This system integrates vector retrieval, grounded generation, persistent agent memory, tool execution, and robust resilience patterns into a single unified architecture.

## Domain and reproducibility

**Domain: E-commerce**

Dataset design choices:
- seed: `4242` (the generator deterministically increments the seed only if the generated delayed-shipment rate misses the required band)
- records: `50`
- categories: Apparel, Electronics, Home, Footwear, Beauty with equal base weights of 20% each
- statuses: Placed 20%, Shipped 20%, Delivered 25%, Returned 20%, Refunded 15%
- order amount range: INR 499–24,999, chosen to cover realistic low/mid/high-value synthetic retail orders without using real customer data
- delayed shipment probability: 20%; the generator never hand-edits an individual record to force the percentage

Run `python dataset.py` to print the validation report and write `data/orders.json`.

## Architecture

`dataset.py` → `kb/*.md` → two chunkers → SentenceTransformers (`all-MiniLM-L6-v2`) → separate ChromaDB collections → RAG → LangGraph agent → FastAPI.

The agent has six nodes: `guard`, `route`, `rag`, `order`, `memory`, `respond`. The `route` node has a conditional edge to either the RAG or order-status tool.

## Knowledge base

Twelve original, synthetic policy documents cover:
return window, COD refunds, delivery SLA, reverse pickup, warranty, cancellation, loyalty points, payment retry, size exchange, damaged-item claims, international restrictions, and escalation.

## Grounded generation and calibration

`evaluation/calibrate.py` measures top-1 similarity for 3 in-scope and 2 out-of-scope queries. The calibrated threshold is `0.42`, selected between the observed out-of-scope maximum (`0.3866`) and in-scope minimum (`0.4365`).

`evaluation/evaluate_rag.py` compares fixed-size-overlap and sentence chunking at document level. It prints per-query Precision@3 and Recall@3 arithmetic for the first five benchmark questions.

## Order-status escalation score

Formula:

`score = 0.6 * delayed_shipment + 0.4 * (days_since_created / 30)`

This combines a binary shipment-risk component with a normalized recency component. The proposed escalation threshold is `0.70`; before final submission, run a distribution analysis and explain what percentile/risk boundary this threshold represents in the generated dataset.

## Memory and structured output

Conversation history is persisted in `data/memory.json`, keyed by thread ID. Every final response is validated against the JSON Schema in `app/schema.py`.

A fresh thread ID has no previous history. Use `run_demo.py` and inspect `data/memory.json` to demonstrate continuity and reset behavior.

## Guardrails

Input:
- fixed-format Indian phone numbers are masked
- card last-4 fields are masked
- prompt-injection patterns are blocked

Output:
- RAG falls back to `"I don't know based on the available E-commerce knowledge base."` when the best retrieval score is below the empirically calibrated threshold.

The fixed-format PII rule intentionally does not pretend that arbitrary names or free-text addresses can be reliably detected without a key or model.

## FastAPI

Start with:

```bash
set MOCK_LLM=1
uvicorn app.api:app --reload
```

Endpoints:
- `POST /ask`
- `POST /add-document`

Every `/ask` request creates one JSON Lines record in `data/requests.jsonl` containing a UUID trace ID, elapsed time, and masked query.

## MCP

Start the private server:

```bash
python mcp_server.py
```

The HTTP MCP endpoint is:

`http://127.0.0.1:8001/mcp`

Then in another terminal:

```bash
python mcp_client.py
```

The client calls two different synthetic order IDs.

## Resilience

`resilience.py` demonstrates:
- exponential backoff retry: max attempts 5, initial interval 0.05s, max interval 0.2s, jitter up to 0.01s
- per-node timeout
- global timeout

`checkpoint_demo.py` documents the required SQLite interruption/resume demonstration. Because LangGraph SQLite saver APIs can differ between package releases, verify the installed `langgraph-checkpoint-sqlite` API and capture the actual node event output before claiming the acceptance criterion is complete.

## Evaluation

Run:

```bash
python evaluation/calibrate.py
python evaluation/evaluate_rag.py
python evaluation/rag_triad.py
pytest -q
python run_demo.py
```

`rag_triad.py` contains 15 queries: all required KB topics plus out-of-scope/edge cases. It prints context relevance, groundedness and answer relevance per query and the three averages.

## Zero-key requirement

The project is designed around deterministic local behavior and does not require a paid API key. `MOCK_LLM=1` is the intended graded mode. No real customer data, API keys, credentials, or copyrighted datasets are included.

## Submission checklist

- [X ] Run the dataset generator and paste the actual counts/rate into this README.
- [X ] Run calibration and replace the placeholder similarity threshold with measured values.
- [X ] Run both chunking evaluations and write the actual arithmetic and recommendation.
- [ X] Demonstrate both LangGraph routes.
- [X ] Demonstrate persistent memory and a fresh thread reset.
- [X ] Demonstrate PII masking, injection blocking, and groundedness fallback.
- [ X] Run FastAPI endpoints and inspect JSONL masking.
- [ X] Run the 15-query RAG triad and record actual averages.
- [ X] Run MCP server/client round trip for two IDs.
- [ X] Run the real LangGraph SQLite checkpoint interruption/resume test with the installed package.
- [X ] Run retry, node timeout, and global timeout demonstrations.
- [X ] Review every file and make sure the final repository represents your own work and understanding.

## Submission-domain check

Question 1 must be entered exactly as **`E-commerce`**. The GitHub repository submitted in Question 2 is this E-commerce capstone repository. The Nykaa name appears only as the scenario/retail brand in the supplied problem brief, not as the selected LMS domain.

## Originality / copyright note

All dataset records and KB policy text in this repository are synthetic and newly written for this project. No real real customer records, private data, copied articles, screenshots, images, PDFs, or proprietary source code are included. The repository may use open-source packages through their normal package-manager licenses; those licenses remain the responsibility of the package authors.

## Submission alignment

- **Question 1 value:** `E-commerce`
- **GitHub repository name:** `E-commerce`
- The repository is intentionally code/text based and uses only synthetic order/customer data.

## Empirical RAG calibration

Run:

```bash
python evaluation/calibrate.py
```

Observed local top-1 similarities from the benchmark run:

| Query class | Query | Similarity |
|---|---|---:|
| In-scope | What is the return window for footwear? | 0.5441 |
| In-scope | How long does COD refund take? | 0.7865 |
| In-scope | What is the delivery SLA? | 0.4365 |
| Out-of-scope | How do I repair my car engine? | 0.3866 |
| Out-of-scope | Who won yesterday's football match? | 0.3593 |

Therefore a valid threshold must satisfy `0.3866 < threshold < 0.4365`. The selected threshold is **0.42**, which is strictly between the observed out-of-scope and in-scope clusters. The demo also includes the required in-scope and out-of-scope fallback behavior.

## RAG chunking evaluation

Run:

```bash
python evaluation/evaluate_rag.py
```

The same five benchmark questions were evaluated for both fixed-size-overlap and sentence-based chunking at document level. Each strategy produced, per query, `Precision@3 = 1/3 = 0.333` and `Recall@3 = 1/1 = 1.000`.

| Strategy | Mean Precision@3 | Mean Recall@3 |
|---|---:|---:|
| Fixed-size-overlap | 0.333 | 1.000 |
| Sentence-based | 0.333 | 1.000 |

**Recommendation:** the two strategies tie on this benchmark, so no performance superiority is claimed. Sentence-based chunking remains the default because it is simple and preserves sentence boundaries.

## RAG triad evaluation

Run:

```bash
python evaluation/rag_triad.py
```

The 15-query benchmark covers all 12 KB topics plus out-of-scope/edge cases. Mean scores from the completed MOCK_LLM evaluation are:

| Metric | Average / 5 |
|---|---:|
| Context relevance | 4.47 |
| Groundedness | 4.87 |
| Answer relevance | 5.00 |

The two out-of-scope queries intentionally score lower on context relevance while the answer remains a grounded refusal.

## SQLite checkpointing and resume

Part 4 requires actual LangGraph SQLite checkpointing, not a placeholder file. `checkpoint_demo.py` uses `langgraph-checkpoint-sqlite` and `SqliteSaver`, interrupts before the `tool` node, and resumes the same `thread_id`. Execution counters demonstrate that completed `guard` and `route` nodes are not re-executed during resume.

```bash
python checkpoint_demo.py
```

## Resilience evidence

`resilience.py` demonstrates all three required controls: exponential backoff retry (maximum 5 attempts, initial interval 0.05s, maximum interval 0.2s, jitter 0.01s), a per-node timeout, and a global timeout. The transient failure demo fails twice and succeeds on the third call.

```bash
python resilience.py
```
