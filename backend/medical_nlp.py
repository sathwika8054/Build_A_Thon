import re


DISEASES = [
    "dengue",
    "malaria",
    "influenza",
    "covid",
    "covid-19",
    "diabetes",
    "hypertension",
    "pneumonia"
]

INTENTS = {
    "symptoms": [
        "symptom",
        "symptoms",
        "sign",
        "signs",
        "feel",
        "feeling"
    ],
    "prevention": [
        "prevent",
        "prevention",
        "avoid",
        "protect"
    ],
    "transmission": [
        "spread",
        "spreads",
        "transmission",
        "transmitted",
        "catch"
    ],
    "warning_signs": [
        "danger",
        "dangerous",
        "warning",
        "emergency",
        "serious",
        "severe"
    ],
    "treatment": [
        "treatment",
        "treat",
        "cure",
        "medicine"
    ]
}


def extract_medical_concepts(query: str):

    text = query.lower()

    # Find disease
    detected_disease = None

    for disease in DISEASES:
        if disease in text:
            detected_disease = disease
            break

    # Find intent
    detected_intent = "general"

    for intent, keywords in INTENTS.items():

        for keyword in keywords:

            if keyword in text:
                detected_intent = intent
                break

        if detected_intent != "general":
            break

    # Find symptoms
    symptom_patterns = [
        r"fever",
        r"cough",
        r"headache",
        r"vomiting",
        r"nausea",
        r"rash",
        r"fatigue",
        r"body pain",
        r"body ache",
        r"sore throat",
        r"breathing"
    ]

    detected_symptoms = []

    for pattern in symptom_patterns:

        if re.search(pattern, text):
            detected_symptoms.append(pattern)

    return {
        "disease": detected_disease,
        "intent": detected_intent,
        "symptoms": detected_symptoms,
        "original_query": query
    }