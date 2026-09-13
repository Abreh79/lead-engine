import os
import sys
import argparse
import re
from db import get_all_leads, get_lead_by_id, init_db

def get_default_base_url():
    # 1. Check if tunnel.log exists with active trycloudflare URL
    tunnel_log = "/home/yayock79/lead_engine/tunnel.log"
    if os.path.exists(tunnel_log):
        with open(tunnel_log, "r") as f:
            content = f.read()
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
            if match:
                return match.group(0)
                
    # 2. Check environment variable
    if os.getenv("BASE_URL"):
        return os.getenv("BASE_URL").rstrip("/")

    # 3. Default fallback
    return "http://localhost:8080"

def generate_cold_sms(business_name, phone, lead_id, base_url):
    preview_url = f"{base_url.rstrip('/')}/preview/{lead_id}"
    sms = f"Hey {business_name}, noticed your site isn't mobile-friendly & losing calls. Built a fast mobile version here: {preview_url} Want me to send the files over?"
    
    if len(sms) > 200:
        sms = f"Hey {business_name}, your site is broken on mobile. Built a clean 2026 version here: {preview_url} Want the files?"
        
    if len(sms) > 200:
        sms = f"Hi {business_name}, saw your site is broken on mobile. Made a fast preview for you: {preview_url} Want the files?"
        
    return sms

def generate_cold_email(business_name, phone, niche, lead_id, base_url):
    preview_url = f"{base_url.rstrip('/')}/preview/{lead_id}"
    email = f"Subject: Mobile site mockup for {business_name}\n\n"
    email += f"Hey {business_name} team, while looking up local {niche} pros in Minneapolis, I noticed your site has mobile responsiveness issues that cause prospective clients to bounce.\n"
    email += f"I put together a fast, mobile-first preview site tailored for your business here: {preview_url}\n"
    email += f"No pressure at all—if you like the layout, I'm happy to hand over the files or help you put it live."
    return email

def build_outreach_queue(base_url=None, output_path="/home/yayock79/lead_engine/outreach_queue.md"):
    if not base_url:
        base_url = get_default_base_url()
        
    init_db()
    leads = get_all_leads(only_broken=True)
    
    md_content = "# LOCAL SERVICE COLD OUTREACH QUEUE 🎯\n\n"
    md_content += f"**Active Public Base URL**: `{base_url}`\n"
    md_content += f"Generated on broken mobile contractor targets ({len(leads)} total qualified leads).\n\n"
    
    target_pitch = None
    
    for l in leads:
        lead_id = l[0]
        name = l[1]
        niche = l[2]
        phone = l[3]
        url = l[4]
        
        sms = generate_cold_sms(name, phone, lead_id, base_url)
        email = generate_cold_email(name, phone, niche, lead_id, base_url)
        
        if lead_id == 31 or "Metro Emergency" in name or target_pitch is None:
            target_pitch = {
                "id": lead_id,
                "name": name,
                "phone": phone,
                "sms": sms,
                "email": email,
                "base_url": base_url
            }
        
        md_content += f"## Lead #{lead_id}: {name} [{niche}]\n"
        md_content += f"- **Phone**: {phone}\n"
        md_content += f"- **Original URL**: {url}\n"
        md_content += f"- **Public Mobile Preview Link**: {base_url}/preview/{lead_id}\n\n"
        md_content += "### 📱 COLD SMS (Under 200 Chars)\n"
        md_content += f"```\n{sms}\n```\n"
        md_content += f"*(Char Count: {len(sms)} chars)*\n\n"
        md_content += "### 📧 3-SENTENCE COLD EMAIL\n"
        md_content += f"```\n{email}\n```\n\n"
        md_content += "---\n\n"
        
    with open(output_path, "w") as f:
        f.write(md_content)
        
    print(f"[OUTREACH] Saved outreach queue with base URL '{base_url}' to: {output_path}")
    return target_pitch

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate cold outreach pitches with custom base URL.")
    parser.add_argument("--base-url", type=str, help="Public domain or Cloud Shell / Cloudflare tunnel base URL")
    args = parser.parse_args()
    
    selected_url = args.base_url if args.base_url else get_default_base_url()
    pitch = build_outreach_queue(base_url=selected_url)
    
    if pitch:
        print("\n==================================================")
        print(f"GENERATED PUBLIC OUTREACH PITCH FOR LEAD #{pitch['id']}: {pitch['name']}")
        print("==================================================")
        print(f"🌐 PUBLIC BASE URL: {pitch['base_url']}")
        print("\n📱 COLD SMS (Under 200 chars):")
        print(pitch['sms'])
        print(f"(Length: {len(pitch['sms'])} chars)")
        print("\n📧 3-SENTENCE COLD EMAIL:")
        print(pitch['email'])
        print("==================================================")
