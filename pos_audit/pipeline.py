try:
    from .analyzer import analyze_merchant_statement
    from .parser import generate_audit_memo
    from .generator import generate_demand_letter, dispatch_iso_lead
except ImportError:
    from analyzer import analyze_merchant_statement
    from parser import generate_audit_memo
    from generator import generate_demand_letter, dispatch_iso_lead

def run_pipeline(mock_payload: dict, webhook_url: str = None):
    print("\n[+] Step 1: Running Forensic Math Analysis...")
    analysis = analyze_merchant_statement(mock_payload)
    
    print("\n[+] Step 2: Generating Audit Memo...")
    audit_memo = generate_audit_memo(analysis)
    print(audit_memo)
    
    print("\n[+] Step 3: Drafting Retention Demand Letter...")
    letter = generate_demand_letter(mock_payload, analysis)
    print(letter)
    
    if analysis["verdict"] == "PRIORITY TARGET":
        print("[!] Priority target detected ($1,500+/yr savings).")
        if webhook_url:
            print(f"[+] Dispatching lead to ISO CRM at {webhook_url}...")
            res = dispatch_iso_lead(mock_payload, analysis, webhook_url)
            print(f"    Dispatch status: {res}")
        else:
            print("    (No webhook URL configured; skipping dispatch)")

if __name__ == "__main__":
    sample_merchant = {
        "business_name": "Midwest Auto Spa LLC",
        "gross_processing_volume": 62400.00,
        "transaction_count": 1850,
        "total_fees_charged": 2215.20,
        "cost_breakdown": {
            "wholesale_interchange_assessments": 1092.00,
            "processor_markup_basis_points_dollars": 1023.25,
            "ancillary_junk_fees": [
                {"fee_name": "PCI Non-Validation Fee", "amount": 49.95},
                {"fee_name": "Monthly Portal / Regulatory Fee", "amount": 25.00},
                {"fee_name": "Batch Settlement Surcharge", "amount": 25.00}
            ]
        },
        "terminal_hardware_hints": ["Clover Station Solo", "Clover Flex"]
    }
    
    run_pipeline(sample_merchant)
