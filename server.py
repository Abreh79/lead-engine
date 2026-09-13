from flask import Flask, render_template, abort, jsonify
from db import get_lead_by_id, get_all_leads, init_db

app = Flask(__name__)

@app.route("/")
def index():
    init_db()
    leads = get_all_leads()
    html_out = "<h1>Local Service Client Acquisition Engine - Preview Server</h1>"
    html_out += "<ul>"
    for l in leads:
        lead_id = l[0]
        name = l[1]
        niche = l[2]
        phone = l[3]
        broken = "🚨 Broken Mobile" if l[9] else "✅ Mobile Ready"
        html_out += f"<li><a href='/preview/{lead_id}' target='_blank'><strong>[{niche}] {name}</strong></a> ({phone}) - {broken}</li>"
    html_out += "</ul>"
    return html_out

@app.route("/preview/<int:lead_id>")
def preview_lead(lead_id):
    init_db()
    lead = get_lead_by_id(lead_id)
    if not lead:
        abort(404, description=f"Lead with ID {lead_id} not found in database.")
    return render_template("landing_page.html", lead=lead)

@app.route("/api/leads")
def api_leads():
    init_db()
    leads = get_all_leads()
    return jsonify([dict(zip(["id", "business_name", "niche", "phone", "website_url", "review_count", "has_viewport", "http_status", "load_speed_sec", "is_broken_mobile"], l)) for l in leads])

if __name__ == "__main__":
    init_db()
    print("Starting Preview Server on http://0.0.0.0:8080...")
    app.run(host="0.0.0.0", port=8080, debug=False)
