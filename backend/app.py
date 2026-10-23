import os
import json
import re
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pos-audit-engine")

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["https://studio-7106835876-c5253.web.app", "http://localhost:8080", "*"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"]
}})

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    return genai.Client()

SYSTEM_PROMPT = """You are an expert merchant payment processing forensic auditor.
Analyze the attached merchant processing statement (PDF or image).

Parsing & Extraction Instructions:
1. Locate the summary ledger (Total Gross Amount Submitted / Total Volume, Total Transactions, Total Fees / Charges).
2. For multi-account or multi-location statements (e.g. First Data, Clover, Wells Fargo, Heartland, Chase Paymentech):
   - Explicitly locate and sum the "Total Fees Charged", "Service Charges", "Interchange Charges", or "Total Amount Debited" across ALL merchant IDs and sub-accounts in the PDF.
   - Sum the total gross volume across all sub-accounts.
3. Identify all itemized junk fees / ancillary fees, specifically looking for:
   - PCI non-compliance or PCI validation fees
   - Statement delivery or paper statement fees
   - Monthly advantage or account maintenance fees
   - Digital commerce, gateway, or software fees
   - Monthly location or regulatory product fees
   - Any non-interchange fixed fees or monthly add-on fees

Output strictly a JSON object with this exact key structure and data types:
{
  "volume": <float, total dollar volume processed, e.g. 125000.50>,
  "transactions": <int, total transaction count, e.g. 450>,
  "total_fees": <float, total fees charged by processor, e.g. 3125.00>,
  "ancillary_fees": <float, sum of all junk/ancillary fee amounts, e.g. 150.00>,
  "effective_rate": <float, percentage calculated as (total_fees / volume) * 100 rounded to 2 decimal places, e.g. 2.50>,
  "processor_name": <string, payment processor name e.g. First Data, Clover, Worldpay, Square, Stripe, Heartland, Fiserv, etc.>,
  "statement_period": <string, statement month/year or range e.g. "08/2026">,
  "merchant_name": <string, legal or DBA name of merchant from statement header>,
  "junk_fee_items": [
    {
      "description": <string, fee description>,
      "amount": <float, fee amount>
    }
  ]
}

Rules:
- Default missing numeric fields to 0.0 or 0. Default missing string fields to "Unknown".
- Ensure junk_fee_items is a list of objects with "description" (str) and "amount" (float).
- Do NOT wrap in markdown code blocks or return any text outside the valid JSON object.
"""

def generate_with_fallback(client, part, prompt):
    model_candidates = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    for model_name in model_candidates:
        try:
            logger.info(f"Attempting Gemini call with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=[part, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            if response and response.text:
                return response.text.strip(), model_name
        except Exception as ex:
            logger.warning(f"Model {model_name} failed: {ex}")
    return None, None

def parse_json_response(raw_text):
    if not raw_text:
        return {}
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
    return json.loads(cleaned)

@app.route("/health", methods=["GET"])
@app.route("/api/audit/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "pos-audit-engine"}), 200

@app.route("/api/audit/upload", methods=["POST"])
@app.route("/upload", methods=["POST"])
@app.route("/", methods=["POST"])
def audit_upload():
    try:
        file_obj = None
        if "statement" in request.files:
            file_obj = request.files["statement"]
        elif "file" in request.files:
            file_obj = request.files["file"]
        
        if not file_obj or file_obj.filename == "":
            return jsonify({"error": "No statement or file provided in request"}), 400

        file_bytes = file_obj.read()
        if not file_bytes:
            return jsonify({"error": "Uploaded file is empty"}), 400

        filename = (file_obj.filename or "statement.pdf").lower()
        content_type = file_obj.content_type or "application/pdf"
        
        if filename.endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename.endswith((".png", ".webp")):
            mime_type = "image/png"
        elif filename.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        else:
            mime_type = content_type

        logger.info(f"Processing uploaded file '{file_obj.filename}' ({len(file_bytes)} bytes, mime_type={mime_type})")

        client = get_genai_client()
        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        raw_text, used_model = generate_with_fallback(client, part, SYSTEM_PROMPT)
        if not raw_text:
            return jsonify({"error": "Failed to get response from Gemini Vision models"}), 500

        data = parse_json_response(raw_text)

        volume = float(data.get("volume") or 0.0)
        transactions = int(data.get("transactions") or 0)
        total_fees = float(data.get("total_fees") or 0.0)
        processor_name = str(data.get("processor_name") or "Unknown")
        statement_period = str(data.get("statement_period") or "Unknown")
        merchant_name = str(data.get("merchant_name") or "Unknown")
        
        raw_junk_items = data.get("junk_fee_items") or []
        junk_fee_items = []
        for item in raw_junk_items:
            if isinstance(item, dict):
                desc = str(item.get("description") or "Junk Fee")
                amt = float(item.get("amount") or 0.0)
                junk_fee_items.append({"description": desc, "amount": amt})

        # Sanity Validation Second Pass if volume > 1000 and total_fees == 0
        if volume > 1000.0 and total_fees == 0.0:
            logger.warning(f"Sanity alert: Volume is ${volume:,.2f} but total_fees is $0.00. Executing second-pass fee search.")
            second_pass_prompt = f"""URGENT FORENSIC AUDIT RE-PARSING INSTRUCTION:
Gross volume was detected as ${volume:,.2f}, but Total Fees was extracted as $0.00.
Re-examine every page of the attached statement specifically targeting lines labeled:
- "TOTAL FEES"
- "TOTAL FEES CHARGED"
- "SERVICE CHARGES / INTERCHANGE CHARGES"
- "TOTAL AMOUNT DEBITED"
- "FEES PAID / CHARGED"
Return the complete updated JSON object with the exact total fees numeric value.
"""
            raw_text_2, _ = generate_with_fallback(client, part, second_pass_prompt)
            if raw_text_2:
                data2 = parse_json_response(raw_text_2)
                fees2 = float(data2.get("total_fees") or 0.0)
                if fees2 > 0:
                    logger.info(f"Second pass successfully located total_fees: ${fees2:,.2f}")
                    total_fees = fees2
                    if not junk_fee_items and data2.get("junk_fee_items"):
                        junk_fee_items = [{"description": str(i.get("description") or "Junk Fee"), "amount": float(i.get("amount") or 0.0)} for i in data2["junk_fee_items"] if isinstance(i, dict)]

        calculated_junk_sum = round(sum(item["amount"] for item in junk_fee_items), 2)
        
        effective_rate = float(data.get("effective_rate") or 0.0)
        if effective_rate == 0.0 and volume > 0 and total_fees > 0:
            effective_rate = round((total_fees / volume) * 100, 2)

        processor_spread = round(max(0.0, total_fees - calculated_junk_sum), 2)
        
        status_flag = "success"
        warning_msg = None
        if volume > 1000.0 and total_fees == 0.0:
            status_flag = "partial_extraction"
            warning_msg = "Volume detected but total fees could not be parsed automatically. Please review fee summary on statement."

        analysis_text = f"Audited {statement_period} statement for {merchant_name}. Identified {len(junk_fee_items)} ancillary junk line items totaling ${calculated_junk_sum:,.2f}."
        if warning_msg:
            analysis_text += f" [WARNING: {warning_msg}]"

        result = {
            "status": status_flag,
            "warning": warning_msg,
            "merchant_name": merchant_name,
            "processor_name": processor_name,
            "statement_period": statement_period,
            "volume": float(volume),
            "transactions": int(transactions),
            "total_fees": float(total_fees),
            "effective_rate": float(effective_rate),
            "cost_breakdown": {
                "ancillary_junk_fees": float(calculated_junk_sum),
                "processor_spread": float(processor_spread)
            },
            "junk_fee_items": junk_fee_items,
            "analysis": analysis_text,
            "ancillary_fees": float(calculated_junk_sum),
            "data": {
                "gross_processing_volume": float(volume),
                "transaction_count": int(transactions),
                "total_fees_charged": float(total_fees),
                "ancillary_fees": float(calculated_junk_sum),
                "effective_rate": float(effective_rate),
                "processor_name": processor_name,
                "statement_period": statement_period,
                "merchant_name": merchant_name,
                "junk_fees": junk_fee_items,
                "cost_breakdown": {
                    "ancillary_junk_fees": float(calculated_junk_sum),
                    "processor_spread": float(processor_spread)
                }
            }
        }

        return jsonify(result), 200

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": f"Failed to parse model JSON output: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Audit processing error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
