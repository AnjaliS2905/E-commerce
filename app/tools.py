from dataset import ORDERS

def check_order_status(record_id: str) -> dict:
    """Look up a fabricated order and calculate a continuous escalation score.

    Formula = 0.6 * delayed_shipment + 0.4 * (days_since_created / 30).
    Escalate when score >= 0.70. The threshold is intentionally documented
    and can be recalibrated from the generated distribution.
    """
    rec=next((r for r in ORDERS if r["record_id"]==record_id),None)
    if not rec:
        raise KeyError(f"Unknown record_id: {record_id}")
    score=round(0.6*int(rec["delayed_shipment"])+0.4*(rec["days_since_created"]/30),3)
    return {"record_id":record_id,"status":rec["status"],
            "order_value_inr":rec["order_value_inr"],"escalation_score":score}
