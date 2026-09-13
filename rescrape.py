import sys
from db import wipe_leads
from main import run_lead_pipeline

if __name__ == "__main__":
    print("--- WIPING AGGREGATE DIRECTORY LEADS ---")
    wipe_leads()
    print("\n--- RESCRAPING INDEPENDENT HVAC CONTRACTORS ---")
    run_lead_pipeline("HVAC", "Minneapolis")
    print("\n--- RESCRAPING INDEPENDENT PLUMBING CONTRACTORS ---")
    run_lead_pipeline("Plumbing", "Minneapolis")
