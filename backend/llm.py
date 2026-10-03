# llm.py
# ─────────────────────────────────────────────────────────────────────────────
# This file does ONE job:
#   Send a patient sentence to the local Qwen AI model
#   Get back a clean list of recognised symptoms
#
# The AI does NOT diagnose anything.
# Its only job is: natural language → canonical symptom names from our list.
# ─────────────────────────────────────────────────────────────────────────────

import requests   # lets Python make web requests (to local Ollama server)
import json       # lets Python read and write JSON data
import re         # lets Python search and clean text

# ── Official 23-symptom vocabulary ───────────────────────────────────────────
# These are the ONLY symptom names the system understands.
# The AI must return names from this exact list.
SUPPORTED_SYMPTOMS = [
    "Fever",
    "Chills / shivering",
    "Fatigue / weakness",
    "Body aches",
    "Joint pain",
    "Headache",
    "Loss of appetite",
    "Weight loss",
    "Night sweats",
    "Runny nose",
    "Sneezing",
    "Blocked / stuffy nose",
    "Sore throat",
    "Cough (dry or with phlegm)",
    "Shortness of breath",
    "Wheezing",
    "Chest tightness",
    "Chest pain",
    "Nausea",
    "Vomiting",
    "Constipation",
    "Abdominal pain / cramps",
    "Difficulty swallowing"
]

# ── Instructions we give to the AI ───────────────────────────────────────────
# This is called a "system prompt".
# It defines the AI's role and the rules it must follow.
SYMPTOM_LIST = ", ".join(SUPPORTED_SYMPTOMS)

# ── Instructions we give to the AI ───────────────────────────────────────────
SYSTEM_PROMPT = (
    f"Extract symptoms from patient text. "
    f"Return ONLY this JSON: {{\"symptoms\": [...]}} "
    f"Use ONLY these exact names: {SYMPTOM_LIST}. "
    f"Map natural language: feverish→Fever, exhausted→Fatigue/weakness, tummy hurts→Abdominal pain/cramps, etc. "
    f"No explanation. No extra text. JSON only."
)


SYMPTOM_PATTERNS = {
    "Fever": [r"\bfever\b", r"\btemperature\b", r"\bfeeling hot\b", r"\brunning a temp\b", r"\bhigh fever\b", r"\bburning up\b", r"\bfeverish\b"],
    "Chills / shivering": [r"\bchills\b", r"\bshivering\b", r"\bshivers\b", r"\bfeeling cold\b", r"\bcold shakes\b"],
    "Fatigue / weakness": [r"\bfatigue\b", r"\btired\b", r"\btiredness\b", r"\bexhausted\b", r"\bexhaustion\b", r"\bno energy\b", r"\blethargic\b", r"\bweakness\b"],
    "Body aches": [r"\bmuscle ache\b", r"\bmuscle aches\b", r"\bbody ache\b", r"\bbody aches\b", r"\bmuscles hurt\b", r"\baching body\b", r"\bbody is sore\b"],
    "Joint pain": [r"\bjoint pain\b", r"\bpain in (?:my )?joints\b", r"\baching joints\b", r"\bknees hurt\b", r"\belbows hurt\b"],
    "Headache": [r"\bheadache\b", r"\bhead hurts\b", r"\bhead aching\b", r"\bpain in (?:my )?head\b", r"\bthrobbing head\b"],
    "Loss of appetite": [r"\bloss of appetite\b", r"\bno appetite\b", r"\bdon'?t feel like eating\b", r"\bnot hungry\b", r"\blost (?:my )?appetite\b"],
    "Runny nose": [r"\brunny nose\b", r"\bcold nose\b", r"\bnose is running\b"],
    "Blocked / stuffy nose": [r"\bstuffy nose\b", r"\bblocked nose\b", r"\bcongestion\b"],
    "Sore throat": [r"\bsore throat\b", r"\bthroat hurts\b", r"\bpain in (?:my )?throat\b", r"\bscratchy throat\b", r"\bthroat pain\b"],
    "Cough (dry or with phlegm)": [r"\bcough\b", r"\bcoughing\b", r"\bhack(?:ing)?\b", r"\bdry cough\b", r"\bwet cough\b"],
    "Shortness of breath": [r"\bshortness of breath\b", r"\bdifficulty breathing\b", r"\bhard to breathe\b", r"\btrouble breathing\b", r"\bbreathless\b", r"\bcan'?t breathe\b"],
    "Wheezing": [r"\bwheezing\b", r"\bwheeze\b", r"\bwhistling (?:sound when )?breath(?:ing)?\b"],
    "Chest tightness": [r"\btightness in (?:my )?chest\b", r"\bchest tightness\b", r"\bheavy chest\b"],
    "Chest pain": [r"\bchest pain\b", r"\bpain in (?:my )?chest\b", r"\bchest hurts\b"],
    "Nausea": [r"\bnausea\b", r"\bnauseous\b", r"\bfeel(?:ing)? sick to (?:my )?stomach\b", r"\bqueasy\b"],
    "Vomiting": [r"\bvomiting\b", r"\bvomit\b", r"\bthrowing up\b", r"\bthrew up\b", r"\bpuking\b"],
    "Constipation": [r"\bconstipation\b", r"\bconstipated\b", r"\bcan'?t poop\b"],
    "Abdominal pain / cramps": [r"\babdominal pain\b", r"\bstomach hurts\b", r"\bstomach pain\b", r"\btummy hurts\b", r"\bcramps\b", r"\bstomach ache\b"],
    "Difficulty swallowing": [r"\bdifficulty swallowing\b", r"\bhard to swallow\b", r"\bpainful to swallow\b", r"\bcan'?t swallow\b"],
    "Sneezing": [r"\bsneezing\b", r"\bsneeze\b"],
    "Weight loss": [r"\bweight loss\b", r"\blosing weight\b"],
    "Night sweats": [r"\bnight sweats\b", r"\bsweating at night\b", r"\bwaking up sweaty\b"]
}

def fast_keyword_match(text):
    """
    The user's advanced Regex hybrid algorithm!
    Instantly matches natural variations of symptoms without needing the AI.
    """
    found = []
    text_lower = text.lower()
    
    for canonical_symptom, patterns in SYMPTOM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(canonical_symptom)
                break
                
    return list(set(found))


def extract_symptoms_deep(patient_text):
    """
    Send patient text to Qwen and return a validated symptom list.
    Only called as a background process now!
    """
    print("[DEBUG] Waking up Ollama to deeply analyze natural language...")

    # Build the message to send to Ollama
    payload = {
        "model": "qwen3:4b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": patient_text}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
            # NOTE: No num_predict limit — the model must finish its JSON before we read it.
            # NOTE: think:False was removed — this version of Ollama ignores it and the
            #       100-token cutoff was chopping the reply before the JSON was written.
        }
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        reply_text = response.json()["message"]["content"]
        
        print(f"[DEBUG] Raw AI Reply:\n{reply_text}\n")

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Ollama.")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error talking to Ollama: {e}")
        return []

    # ── Clean & Parse the JSON ────────────────────────────────────────────────
    # Qwen3 is a reasoning model. It ALWAYS writes thinking text first,
    # then places the actual JSON answer at the very END of its reply.
    # So we find ALL matches and take the LAST one.
    all_matches = re.findall(r'\{"symptoms"\s*:\s*\[.*?\]\}', reply_text, flags=re.DOTALL)
    
    if not all_matches:
        # Last resort: try to find any JSON-like block with a list
        start = reply_text.rfind('{"symptoms"')
        end   = reply_text.rfind('}')
        if start != -1 and end > start:
            all_matches = [reply_text[start:end+1]]

    if not all_matches:
        print("[ERROR] Could not find the symptoms JSON block in the AI's response.")
        return []

    clean_json = all_matches[-1]  # Always take the LAST occurrence

    try:
        parsed       = json.loads(clean_json)
        raw_symptoms = parsed.get("symptoms", [])
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse extracted JSON.")
        return []

    # ── Validate every symptom against our official list ─────────────────────
    # We NEVER blindly trust the AI.
    # Create a mapping of lowercase names to official canonical names
    SUPPORTED_LOWER = {s.lower(): s for s in SUPPORTED_SYMPTOMS}
    
    validated = []
    for symptom in raw_symptoms:
        # Check against lowercase version to avoid capitalization bugs
        s_lower = str(symptom).lower().strip()
        
        if s_lower in SUPPORTED_LOWER:
            validated.append(SUPPORTED_LOWER[s_lower])
        else:
            print(f"  [discarded – not in vocabulary]: {symptom}")

    return validated


# ── Manual test ───────────────────────────────────────────────────────────────
# Run this file directly to test it:
#   python llm.py
if __name__ == "__main__":
    test_sentence = "I've been feeling feverish, my body aches and I've had a terrible headache."

    print("=" * 52)
    print("CHRONON AI  —  Symptom Extraction Test")
    print("=" * 52)
    print(f"Patient said:\n  {test_sentence}")
    print("\nSending to Qwen... (may take 10-20 seconds first time)")
    print()

    result = extract_symptoms(test_sentence)

    print(f"Extracted symptoms : {result}")
    print("=" * 52)