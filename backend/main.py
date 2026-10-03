# main.py
# ─────────────────────────────────────────────────────────────────────────────
# This is the Flask web server.
# It acts as the bridge between your HTML frontend and the Python backend.
#
# Workflow:
# HTML sends text ──> Flask ──> llm.py ──> prime_engine.py ──> database.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Flask, request, jsonify
from flask_cors import CORS
import llm
import prime_engine
import database

app = Flask(__name__)
# Allow the HTML file to talk to this server even if opened directly in the browser
CORS(app)

def process_symptoms(extracted_symptoms):
    """
    Helper function to run the Math Engine and Database Lookup
    once symptoms are extracted.
    """
    if len(extracted_symptoms) < 2:
        return jsonify({
            "status": "not_enough_symptoms",
            "message": "Not enough symptoms detected. Please provide at least two symptoms.",
            "extracted": extracted_symptoms
        })

    # Prime Engine (Deterministic Math)
    address = prime_engine.calculate_address(extracted_symptoms)
    token = prime_engine.calculate_token(extracted_symptoms)
    
    # Database Lookup
    exact_match = database.lookup_exact_problem(address, token)

    if exact_match:
        return jsonify({
            "status": "exact_match",
            "address": address,
            "token": token,
            "symptoms": extracted_symptoms,
            "result": exact_match
        })

    # Fallback Closest Match
    closest_matches = database.lookup_closest_problems(extracted_symptoms)

    if closest_matches:
        top_matches = closest_matches[:3]
        return jsonify({
            "status": "closest_matches",
            "address": address,
            "token": token,
            "symptoms": extracted_symptoms,
            "matches": [m["problem"] for m in top_matches]
        })

    return jsonify({
        "status": "no_match",
        "address": address,
        "token": token,
        "symptoms": extracted_symptoms,
        "message": "No matching problem contains all entered symptoms."
    })


@app.route("/api/healthcare/fast", methods=["POST"])
def healthcare_fast():
    """
    FAST SCAN: Uses Regex keywords. Returns instantly.
    """
    data = request.json
    patient_text = data.get("text", "")
    
    print("\n" + "="*50)
    print(f"[FAST SCAN] Received Text: '{patient_text}'")
    
    symptoms = llm.fast_keyword_match(patient_text)
    print(f"[FAST SCAN] Detected: {symptoms}")
    
    return process_symptoms(symptoms)


@app.route("/api/healthcare/deep", methods=["POST"])
def healthcare_deep():
    """
    DEEP SCAN: Uses Ollama AI. Takes a few seconds.
    """
    data = request.json
    patient_text = data.get("text", "")
    
    print("\n" + "-"*50)
    print(f"[DEEP AI SCAN] Analyzing: '{patient_text}'")
    
    symptoms = llm.extract_symptoms_deep(patient_text)
    print(f"[DEEP AI SCAN] Detected: {symptoms}")
    
    return process_symptoms(symptoms)

if __name__ == "__main__":
    # Ensure database is initialized before starting server
    print("Initializing Database...")
    database.initialize_database()
    
    print("\nStarting CHRONON AI Backend Server...")
    print("Listening on http://localhost:5000\n")
    # Run the server on port 5000
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
