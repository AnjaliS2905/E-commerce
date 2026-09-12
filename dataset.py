"""Deterministic synthetic E-commerce order dataset.

All values are fabricated for this student project. No customer PII is included.
"""
from collections import Counter
import json, random
from pathlib import Path

SEED = 4242
N_ORDERS = 50
CATEGORY_WEIGHTS = {"Apparel": 0.20, "Electronics": 0.20, "Home": 0.20, "Footwear": 0.20, "Beauty": 0.20}
STATUS_WEIGHTS = {"Placed": .20, "Shipped": .20, "Delivered": .25, "Returned": .20, "Refunded": .15}
AMOUNT_RANGE_INR = (499, 24999)
DELAY_PROBABILITY = .20

def generate_orders(seed=SEED, n=N_ORDERS):
    rng = random.Random(seed)
    categories = list(CATEGORY_WEIGHTS)
    statuses = list(STATUS_WEIGHTS)
    # Stratified base guarantees the required vocabulary/count coverage; the
    # remaining records are sampled deterministically from the stated weights.
    records = []
    for i, c in enumerate(categories):
        records.append({"record_id": f"NYK-{i+1:04d}", "category": c,
                        "status": statuses[i], "order_value_inr": rng.randint(*AMOUNT_RANGE_INR),
                        "days_since_created": rng.randint(0,30),
                        "delayed_shipment": rng.random() < DELAY_PROBABILITY})
    for i in range(len(records), n):
        c = rng.choices(categories, weights=list(CATEGORY_WEIGHTS.values()))[0]
        s = rng.choices(statuses, weights=list(STATUS_WEIGHTS.values()))[0]
        records.append({"record_id": f"NYK-{i+1:04d}", "category": c, "status": s,
                        "order_value_inr": rng.randint(*AMOUNT_RANGE_INR),
                        "days_since_created": rng.randint(0,30),
                        "delayed_shipment": rng.random() < DELAY_PROBABILITY})
    # If the deterministic draw is outside the allowed delay band, regenerate
    # with the documented seed search rule rather than editing records.
    if not .10 <= sum(x["delayed_shipment"] for x in records)/n <= .30:
        return generate_orders(seed + 1, n)
    return records

ORDERS = generate_orders()

def validate_orders(records=ORDERS):
    assert len(records) >= 40
    assert set(CATEGORY_WEIGHTS).issubset({r["category"] for r in records})
    assert set(STATUS_WEIGHTS).issubset({r["status"] for r in records})
    assert all(0 <= r["days_since_created"] <= 30 and isinstance(r["days_since_created"], int) for r in records)
    cats, sts = Counter(r["category"] for r in records), Counter(r["status"] for r in records)
    assert all(cats[c] >= 3 for c in CATEGORY_WEIGHTS)
    pct = sum(r["delayed_shipment"] for r in records)/len(records)
    assert .10 <= pct <= .30
    return {"records": len(records), "category_counts": dict(cats),
            "status_counts": dict(sts), "delayed_percentage": round(pct*100,2)}

if __name__ == "__main__":
    report = validate_orders()
    print(json.dumps(report, indent=2))
    Path("data/orders.json").write_text(json.dumps(ORDERS, indent=2))
