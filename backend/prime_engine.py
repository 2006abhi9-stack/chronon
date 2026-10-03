# prime_engine.py
# ─────────────────────────────────────────────────────────────────────────────
# The mathematical core of CHRONON AI's healthcare system.
#
# Every symptom has a unique prime number assigned to it.
# When a patient describes multiple symptoms, we:
#
#   ADDRESS = SUM of their primes   → tells us WHERE to look in the database
#   TOKEN   = PRODUCT of their primes → tells us EXACTLY which combination
#
# This is deterministic: same symptoms → same address + token, always.
# The prime engine does NOT use any AI. It is pure math.
# ─────────────────────────────────────────────────────────────────────────────

# ── Symptom → Prime number mapping ───────────────────────────────────────────
# These values must NEVER be changed.
# The entire database is built on top of this exact mapping.
SYMPTOM_PRIMES = {
    "Fever":                        3,
    "Chills / shivering":           5,
    "Fatigue / weakness":           7,
    "Body aches":                  11,
    "Joint pain":                  13,
    "Headache":                    17,
    "Loss of appetite":            19,
    "Weight loss":                 23,
    "Night sweats":                29,
    "Runny nose":                  31,
    "Sneezing":                    37,
    "Blocked / stuffy nose":       41,
    "Sore throat":                 43,
    "Cough (dry or with phlegm)":  47,
    "Shortness of breath":         53,
    "Wheezing":                    59,
    "Chest tightness":             61,
    "Chest pain":                  67,
    "Nausea":                      71,
    "Vomiting":                    73,
    "Constipation":                79,
    "Abdominal pain / cramps":     83,
    "Difficulty swallowing":       89,
}


def calculate_address(symptoms):
    """
    Calculate the ADDRESS for a list of symptoms.
    ADDRESS = sum of each symptom's prime number.

    Example:
        symptoms = ["Fever", "Headache", "Body aches"]
        primes   = [3, 17, 11]
        address  = 3 + 17 + 11 = 31
    """
    total = 0
    for symptom in symptoms:
        prime = SYMPTOM_PRIMES.get(symptom)
        if prime is not None:
            total += prime
    return total


def calculate_token(symptoms):
    """
    Calculate the TOKEN for a list of symptoms.
    TOKEN = product (multiplication) of each symptom's prime number.

    Example:
        symptoms = ["Fever", "Headache", "Body aches"]
        primes   = [3, 17, 11]
        token    = 3 × 17 × 11 = 561
    """
    product = 1
    for symptom in symptoms:
        prime = SYMPTOM_PRIMES.get(symptom)
        if prime is not None:
            product *= prime
    return product


def get_primes_for_symptoms(symptoms):
    """Return a list of prime values for the given symptom names."""
    return [SYMPTOM_PRIMES[s] for s in symptoms if s in SYMPTOM_PRIMES]


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test = ["Fever", "Headache", "Body aches"]
    print("Symptoms :", test)
    print("Primes   :", get_primes_for_symptoms(test))
    print("Address  :", calculate_address(test))
    print("Token    :", calculate_token(test))
