import os
import sys
from db import get_all_leads, get_lead_by_id, init_db

def generate_cold_sms(business_name, phone, lead_id, base_url="http://localhost:8080"):
    preview_url = f"{base_url}/preview/{lead_id}"
    sms = f"Hey {business_name}, noticed your site isn't mobile-friendly & losing calls. Built a fast mobile version here: {preview_url} Want me to send the files over?"
    if len(sms) > 200:
        sms = f"Hey {business_name}, your site is broken on mobile. Built a clean 2026 version here: {preview_url} Want the files?"
    return sms

def generate_cold_email(business_name, phone, niche, lead_id, base_url="http://localhost:8080"):
    preview_url = f"{base_url}/preview/{lead_id}"
    email = f"Subject: Mobile site mockup for {business_name}\n\n"
    email += f"Hey {business_name} team, while looking up local {niche} pros in Minneapolis, I noticed your site has mobile responsiveness issues that cause prospective clients to bounce.\n"
    email += f"I put together a fast, mobile-first preview site tailored for your business here: {preview_url}\n"
    email += f"No pressure at all—if you like the layout, I'm happy to hand over the files or help you put it live."
    return email

def build_outreach_queue(output_path="/home/yayock79/lead_engine/outreach_queue.md"):
    init_db()
    leads = get_all_leads(only_broken=True)
    
    md_content = "# LOCAL SERVICE COLD OUTREACH QUEUE 🎯\n\n"
    md_content += f"Generated on broken mobile contractor targets ({len(leads)} total qualified leads).\n\n"
    
    target_pitch = None
    
    for l in leads:
        lead_id = l[0]
        name = l[1]
        niche = l[2]
        phone = l[3]
        url = l[4]
        
        sms = generate_cold_sms(name, phone, lead_id)
        email = generate_cold_email(name, phone, niche, lead_id)
        
        if lead_id == 31 or "Metro Emergency" in name or target_pitch is None:
            target_pitch = {
                "id": lead_id,
                "name": name,
                "phone": phone,
                "sms": sms,
                "email": email
            }
        
        md_content += f"## Lead #{lead_id}: {name} [{niche}]\n"
        md_content += f"- **Phone**: {phone}\n"
        md_content += f"- **Original URL**: {url}\n"
        md_content += f"- **Preview Link**: http://localhost:8080/preview/{lead_id}\n\n"
        md_content += "### 📱 COLD SMS (Under 200 Chars)\n"
        md_content += f"```\n{sms}\n```\n"
        md_content += f"*(Char Count: {len(sms)} chars)*\n\n"
        md_content += "### 📧 3-SENTENCE COLD EMAIL\n"
        md_content += f"```\n{email}\n```\n\n"
        md_content += "---\n\n"
        
    with open(output_path, "w") as f:
        f.write(md_content)
        
    print(f"[OUTREACH] Saved outreach queue to: {output_path}")
    return target_pitch

if __name__ == "__main__":
    pitch = build_outreach_queue()
    if pitch:
        print("\n==================================================")
        print(f"GENERATED OUTREACH PITCH FOR LEAD #{pitch['id']}: {pitch['name']}")
        print("==================================================")
        print("📱 COLD SMS (Under 200 chars):")
        print(pitch['sms'])
        print(f"(Length: {len(pitch['sms'])} chars)")
        print("\n📧 3-SENTENCE COLD EMAIL:")
        print(pitch['email'])
        print("==================================================")
