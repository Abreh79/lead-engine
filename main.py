import sys
import os
from db import init_db, save_lead, get_all_leads
from auditor import audit_website
from scraper import fetch_all_targets

def run_lead_pipeline(niche="HVAC", location="Minneapolis"):
    print("==================================================")
    print("LOCAL SERVICE CLIENT ACQUISITION ENGINE v1.0")
    print("==================================================")
    
    init_db()
    
    print(f"\n[STEP 1] Extracting {niche} Contractors in {location}...")
    targets = fetch_all_targets(niche, location)
    print(f"Found {len(targets)} targets for site auditing.\n")
    
    print("[STEP 2] Auditing Mobile Responsiveness & Site Performance...")
    broken_count = 0
    saved_count = 0
    
    for idx, target in enumerate(targets, 1):
        name = target.get("business_name")
        url = target.get("website_url")
        print(f"\n[{idx}/{len(targets)}] Auditing: {name}")
        print(f"  URL: {url}")
        
        audit_res = audit_website(url)
        
        lead_record = {
            "business_name": name,
            "niche": target.get("niche", niche),
            "phone": target.get("phone", "(555) 000-0000"),
            "website_url": url,
            "review_count": target.get("review_count", 0),
            "has_viewport": audit_res.get("has_viewport"),
            "http_status": audit_res.get("http_status"),
            "load_speed_sec": audit_res.get("load_speed_sec"),
            "is_broken_mobile": audit_res.get("is_broken_mobile")
        }
        
        row_id = save_lead(lead_record)
        saved_count += 1
        
        if audit_res.get("is_broken_mobile"):
            broken_count += 1
            print(f"  STATUS: 🚨 QUALIFIED OUTREACH TARGET (Broken Mobile / Slow Site)")
            print(f"  Reason: {audit_res.get('reason')}")
        else:
            print(f"  STATUS: ✅ Mobile Ready ({audit_res.get('load_speed_sec')}s)")

    print("\n==================================================")
    print("AUDIT SUMMARY & OUTREACH TARGETS")
    print("==================================================")
    print(f"Total Sites Audited       : {saved_count}")
    print(f"Qualified Broken Mobile   : {broken_count}")
    print(f"SQLite Database File      : /home/yayock79/lead_engine/leads.db")
    
    all_broken = get_all_leads(only_broken=True)
    print(f"\nSaved Qualified Leads in Database ({len(all_broken)} total):")
    for lead in all_broken[:5]:
        print(f"  - [{lead[2]}] {lead[1]} | Phone: {lead[3]} | URL: {lead[4]}")
    
    print("==================================================")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "HVAC"
    loc_input = sys.argv[2] if len(sys.argv) > 2 else "Minneapolis"
    run_lead_pipeline(niche_input, loc_input)
