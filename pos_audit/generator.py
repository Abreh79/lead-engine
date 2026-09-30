import requests

def generate_demand_letter(extracted_data: dict, analysis: dict) -> str:
    """Creates a razor-sharp fee reduction letter for the merchant to send their current rep."""
    try:
        biz = (extracted_data or {}).get("business_name") or "[Business Name]"
        m = (analysis or {}).get("metrics") or {}
        ic = (analysis or {}).get("recommendations", {}).get("interchange_plus") or {}
        
        cb = (extracted_data or {}).get("cost_breakdown") or {}
        junk_raw = cb.get("ancillary_junk_fees") if isinstance(cb, dict) else []
        if not isinstance(junk_raw, list):
            junk_raw = []
            
        junk_lines = []
        for f in junk_raw:
            if isinstance(f, dict):
                name = f.get('fee_name', 'Fee')
                amt = f.get('amount', 0.0) or 0.0
                try:
                    amt_float = float(amt)
                except (ValueError, TypeError):
                    amt_float = 0.0
                junk_lines.append(f"  - {name}: ${amt_float:.2f}/mo")
        junk_list = "\n".join(junk_lines)
        
        curr_eff = m.get('current_effective_rate_pct', 0.0)
        curr_spread = m.get('current_processor_spread', 0.0)
        gross_vol = m.get('gross_volume', 0.0)
        annual_sav = ic.get('annual_savings', 0.0)

        return f"""
To: Merchant Account Retention / Pricing Department
From: {biz}
Re: Notice of Processing Cost Review & Rate Match Request

We have completed an independent forensic audit of our recent merchant processing statements. 
Our current effective rate has climbed to {curr_eff:.2f}%, representing a processor spread 
of ${curr_spread:,.2f}/mo over baseline interchange on ${gross_vol:,.2f} in volume.

Specifically, we have flagged the following non-negotiable fee concerns:
{junk_list if junk_list else "  - Elevated non-qualified tier margins and padded transaction surcharges"}

We have received a competitive, binding quote for transparent Interchange-Plus pricing at:
  - Interchange + 0.15% (15 bps) + $0.07 per transaction
  - $0.00 ancillary statement/portal/PCI non-compliance fees
  - Projected annual cost reduction: ${annual_sav:,.2f}

We prefer to avoid the operational friction of reprogramming our terminals and re-routing batch 
settlements to a new acquiring partner. However, we require an immediate adjustment to match 
transparent Interchange-Plus terms and waive all assessed junk fees.

Please confirm in writing within 5 business days whether your office will adjust our schedule, 
or provide the formal cancellation procedures for our account.

Sincerely,
{biz} Management
"""
    except Exception as e:
        return f"[Retention Demand Letter Fallback: {e}]"

def dispatch_iso_lead(extracted_data: dict, analysis: dict, webhook_url: str) -> dict:
    """Dispatches a pre-qualified lead payload directly to an ISO partner CRM or webhook."""
    try:
        biz_name = (extracted_data or {}).get("business_name", "Unknown Business")
        m = (analysis or {}).get("metrics") or {}
        ic = (analysis or {}).get("recommendations", {}).get("interchange_plus") or {}
        verdict = (analysis or {}).get("verdict", "STANDARD")
        hints = (extracted_data or {}).get("terminal_hardware_hints") or []
        if not isinstance(hints, list):
            hints = []

        payload = {
            "event": "merchant_audit_completed",
            "priority": verdict,
            "lead_data": {
                "business_name": biz_name,
                "monthly_volume": m.get("gross_volume", 0.0),
                "transaction_count": m.get("total_transactions", 0),
                "current_effective_rate": m.get("current_effective_rate_pct", 0.0),
                "target_annual_savings": ic.get("annual_savings", 0.0),
                "detected_hardware": hints
            }
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return {"status": "dispatched", "status_code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}
