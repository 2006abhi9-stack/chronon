# database.py
# ─────────────────────────────────────────────────────────────────────────────
# This handles the SQL database for CHRONON AI.
# It stores the predefined problem records, medical categories, specialists,
# and dummy doctors.
#
# We use SQLite because it creates a simple local file (chronon.db).
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
import json
import prime_engine

DB_FILE = "chronon.db"

# ── 19 Predefined Prototype Problems ──────────────────────────────────────────
DISEASE_RULES = [
    {"name": "Allergic Rhinitis (Hay Fever)", "category": "Allergy / Immunology", "symptoms": ["Sneezing", "Runny nose"]},
    {"name": "Viral Laryngitis", "category": "ENT", "symptoms": ["Sore throat", "Difficulty swallowing"]},
    {"name": "Asthma Attack / Reactive Airway", "category": "Pulmonology", "symptoms": ["Wheezing", "Shortness of breath"]},
    {"name": "Functional Dyspepsia / Indigestion", "category": "Gastroenterology", "symptoms": ["Nausea", "Abdominal pain / cramps"]},
    {"name": "Common Cold (Viral Upper Respiratory Infection)", "category": "General Practice", "symptoms": ["Runny nose", "Sneezing", "Blocked / stuffy nose"]},
    {"name": "Acute Pharyngitis", "category": "ENT", "symptoms": ["Sore throat", "Difficulty swallowing", "Fever"]},
    {"name": "Acute Bronchitis (Early Stage)", "category": "Pulmonology", "symptoms": ["Cough (dry or with phlegm)", "Chest tightness", "Shortness of breath"]},
    {"name": "Gastroenteritis (Mild)", "category": "Gastroenterology", "symptoms": ["Nausea", "Vomiting", "Abdominal pain / cramps"]},
    {"name": "Acid Reflux / GERD", "category": "Gastroenterology", "symptoms": ["Difficulty swallowing", "Chest tightness", "Sore throat"]},
    {"name": "Acute Bacterial Sinusitis", "category": "ENT", "symptoms": ["Blocked / stuffy nose", "Runny nose", "Headache", "Fever"]},
    {"name": "Chikungunya", "category": "Infectious Disease", "symptoms": ["Fever", "Joint pain", "Body aches", "Fatigue / weakness"]},
    {"name": "Whooping Cough (Pertussis - Early)", "category": "Pulmonology", "symptoms": ["Runny nose", "Sneezing", "Cough (dry or with phlegm)", "Fever"]},
    {"name": "Typhoid Fever", "category": "Infectious Disease", "symptoms": ["Fever", "Fatigue / weakness", "Abdominal pain / cramps", "Constipation"]},
    {"name": "Food Poisoning", "category": "Gastroenterology", "symptoms": ["Nausea", "Vomiting", "Abdominal pain / cramps", "Loss of appetite"]},
    {"name": "Seasonal Influenza (The Flu)", "category": "General Practice", "symptoms": ["Fever", "Chills / shivering", "Body aches", "Fatigue / weakness", "Headache"]},
    {"name": "Dengue Fever", "category": "Infectious Disease", "symptoms": ["Fever", "Headache", "Body aches", "Joint pain", "Nausea"]},
    {"name": "Malaria", "category": "Infectious Disease", "symptoms": ["Fever", "Chills / shivering", "Night sweats", "Headache", "Body aches"]},
    {"name": "Bacterial Pneumonia", "category": "Pulmonology", "symptoms": ["Fever", "Chills / shivering", "Cough (dry or with phlegm)", "Chest pain", "Shortness of breath"]},
    {"name": "COVID-19 / Viral Syndrome", "category": "Infectious Disease", "symptoms": ["Fever", "Body aches", "Fatigue / weakness", "Cough (dry or with phlegm)", "Loss of appetite", "Sore throat"]},
]

# ── Dummy Doctor Database ────────────────────────────────────────────────────
MOCK_DOCTORS = [
    {"name": "Dr. Sarah Jenkins", "specialty": "Allergy / Immunology", "availability": "Available Today"},
    {"name": "Dr. Marcus Chen", "specialty": "ENT", "availability": "Available Tomorrow"},
    {"name": "Dr. Emily Stone", "specialty": "Pulmonology", "availability": "Available in 2 hrs"},
    {"name": "Dr. Rajesh Gupta", "specialty": "Gastroenterology", "availability": "Available Today"},
    {"name": "Dr. Linda Adams", "specialty": "General Practice", "availability": "Walk-in Available"},
    {"name": "Dr. Hassan Tariq", "specialty": "Infectious Disease", "availability": "Available Today"},
]

def initialize_database():
    """Create tables and populate them with the initial 19 problems."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Drop existing tables to start fresh
    cursor.executescript("""
        DROP TABLE IF EXISTS problems;
        DROP TABLE IF EXISTS doctors;
        
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            availability TEXT NOT NULL
        );

        CREATE TABLE problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            symptoms_json TEXT NOT NULL,
            address INTEGER NOT NULL,
            token INTEGER NOT NULL
        );
    """)

    # 1. Insert doctors
    for doc in MOCK_DOCTORS:
        cursor.execute(
            "INSERT INTO doctors (name, specialty, availability) VALUES (?, ?, ?)",
            (doc["name"], doc["specialty"], doc["availability"])
        )

    # 2. Insert predefined problems using the prime engine
    for rule in DISEASE_RULES:
        symptoms = rule["symptoms"]
        address = prime_engine.calculate_address(symptoms)
        token = prime_engine.calculate_token(symptoms)
        
        cursor.execute(
            """INSERT INTO problems 
               (name, category, symptoms_json, address, token) 
               VALUES (?, ?, ?, ?, ?)""",
            (rule["name"], rule["category"], json.dumps(symptoms), address, token)
        )

    conn.commit()
    conn.close()
    print("[DB] Database initialized with problems and doctors.")

def lookup_exact_problem(address, token):
    """
    Look for an exact problem match using the mathematical address and token.
    Returns a dictionary of the problem and a list of matching doctors, or None.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM problems WHERE address = ? AND token = ?", (address, token))
    problem_row = cursor.fetchone()

    if not problem_row:
        conn.close()
        return None

    problem = dict(problem_row)
    problem["symptoms"] = json.loads(problem["symptoms_json"])

    # Find doctors for this category
    cursor.execute("SELECT name, specialty, availability FROM doctors WHERE specialty = ?", (problem["category"],))
    doctors = [dict(row) for row in cursor.fetchall()]

    conn.close()
    
    return {
        "problem": problem,
        "doctors": doctors
    }

def lookup_closest_problems(user_symptoms):
    """
    Fallback: Find problems where ALL the user_symptoms are a subset of the problem's symptoms.
    Now also includes doctor lookups for these fallback matches.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM problems")
    all_problems = cursor.fetchall()
    
    closest_matches = []
    
    for p_row in all_problems:
        p = dict(p_row)
        p_symptoms = json.loads(p["symptoms_json"])
        
        # Check if ALL user symptoms are IN the problem's symptoms
        is_subset = all(symptom in p_symptoms for symptom in user_symptoms)
        
        if is_subset:
            extra_count = len(p_symptoms) - len(user_symptoms)
            p["symptoms"] = p_symptoms
            
            # Fetch doctors for this category
            cursor.execute("SELECT name, specialty, availability FROM doctors WHERE specialty = ?", (p["category"],))
            p["doctors"] = [dict(row) for row in cursor.fetchall()]
            
            closest_matches.append({
                "problem": p,
                "extra_symptoms_count": extra_count
            })
            
    conn.close()
    
    # Sort by the ones that have the fewest extra symptoms (closest match)
    closest_matches.sort(key=lambda x: x["extra_symptoms_count"])
    return closest_matches

if __name__ == "__main__":
    # Test initialization
    initialize_database()
    print("Testing lookup for Address 31, Token 561 (Fever, Headache, Body aches)")
    res = lookup_exact_problem(31, 561) # 3 + 17 + 11 = 31, 3 * 17 * 11 = 561
    print("Result:", res)
