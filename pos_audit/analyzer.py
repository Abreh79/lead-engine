import json
import re

def _safe_float(val, default=0.0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = re.sub(r'[^\d\.\-]', '', val)
        try:
            return float(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default
    return default

def _safe_int(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        cleaned = re.sub(r'[^\d\-]', '', val)
        try:
            return int(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default
    return default

def analyze_merchant_statement(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}

    volume = _safe_float(data.get("gross_processing_volume"), 0.0)
    tx_count = _safe_int(data.get("transaction_count"), 0)
    total_fees = _safe_float(data.get("total_fees_charged"), 0.0)
    
    # Fallback default values if inputs are missing or non-positive
    if volume <= 0:
        volume = 52000.0
    if tx_count <= 0:
        tx_count = max(1, int(volume / 34))
    if total_fees <= 0:
        total_fees = round(volume * 0.0355, 2)

    avg_ticket = volume / max(1, tx_count)
    current_effective_rate = (total_fees / volume) * 100.0 if volume > 0 else 0.0
    
    # Isolate parsed wholesale or estimate realistic blended interchange baseline (1.75% + $0.08)
    breakdown = data.get("cost_breakdown") or {}
    if not isinstance(breakdown, dict):
        breakdown = {}

    interchange = _safe_float(breakdown.get("wholesale_interchange_assessments"), 0.0)
    if interchange <= 0:
        interchange = (volume * 0.0175) + (tx_count * 0.08)
        
    junk_list = breakdown.get("ancillary_junk_fees") or []
    if not isinstance(junk_list, list):
        junk_list = []

    junk_fees = 0.0
    for item in junk_list:
        if isinstance(item, dict):
            junk_fees += _safe_float(item.get("amount"), 0.0)

    processor_spread = max(0.0, total_fees - interchange)

    # Benchmark 1: Transparent Interchange-Plus (IC + 15 bps + $0.07 / tx, zero junk fees)
    ic_plus_markup = (volume * 0.0015) + (tx_count * 0.07)
    ic_plus_total = interchange + ic_plus_markup
    ic_plus_monthly_savings = max(0.0, total_fees - ic_plus_total)
    ic_plus_effective_rate = (ic_plus_total / volume) * 100.0 if volume > 0 else 0.0
    
    # Benchmark 2: Modern Flat Aggregator (e.g., 2.6% + $0.15 / tx)
    flat_rate_total = (volume * 0.026) + (tx_count * 0.15)
    flat_rate_monthly_savings = total_fees - flat_rate_total

    return {
        "metrics": {
            "gross_volume": round(volume, 2),
            "total_transactions": tx_count,
            "average_ticket": round(avg_ticket, 2),
            "current_effective_rate_pct": round(current_effective_rate, 2),
            "identified_junk_fees_monthly": round(junk_fees, 2),
            "current_processor_spread": round(processor_spread, 2)
        },
        "recommendations": {
            "interchange_plus": {
                "estimated_monthly_cost": round(ic_plus_total, 2),
                "estimated_effective_rate_pct": round(ic_plus_effective_rate, 2),
                "monthly_savings": round(ic_plus_monthly_savings, 2),
                "annual_savings": round(ic_plus_monthly_savings * 12, 2)
            },
            "flat_rate_comparison": {
                "estimated_monthly_cost": round(flat_rate_total, 2),
                "monthly_delta": round(flat_rate_monthly_savings, 2)
            }
        },
        "verdict": "PRIORITY TARGET" if (ic_plus_monthly_savings * 12) > 1500 else "STANDARD"
    }
