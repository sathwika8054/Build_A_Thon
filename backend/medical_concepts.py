import re


DISEASES = [
    "dengue",
    "malaria",
    "influenza",
    "covid",
    "covid 19",
    "coronavirus",
    "tuberculosis",
    "typhoid",
    "hepatitis",
    "asthma",
    "diabetes",
    "cholera",
    "pneumonia"
    ,"piles"
    ,"hemorrhoids"
    ,"tonsillitis"
    ,"common cold"
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
        "protect",
        "protection"
    ],

    "transmission": [
        "spread",
        "spreads",
        "transmit",
        "transmitted",
        "transmission",
        "catch"
    ],

    "warning_signs": [
        "warning",
        "danger",
        "severe",
        "emergency",
        "serious"
    ]
}

ALIASES = {
    "flu": "influenza",
    "covid19": "covid",
    "covid-19": "covid",
    "corona": "covid",
    "tb": "tuberculosis",
    "hepatitis b": "hepatitis",
    "hepatitis-b": "hepatitis",
    "asthma attack": "asthma",
    "high sugar": "diabetes"
    ,"hemorrhoid": "piles"
    ,"hemorrhoids": "piles"
    ,"haemorrhoids": "piles"
    ,"piles disease": "piles"
    ,"tonsil": "tonsillitis"
    ,"tonsils": "tonsillitis"
    ,"tonsil infection": "tonsillitis"
    ,"tronsils": "tonsillitis"
    ,"tubercilosis": "tuberculosis"
    ,"tuberculous": "tuberculosis"
    ,"common cold": "common_cold"
    ,"cold": "common_cold"
}


def extract_medical_concepts(query: str):
    query = (query or "").lower()

    concepts = {
        "diseases": [],
        "intent": "general",
        "keywords": []
    }

    normalized_query = re.sub(r"[^a-z0-9\s-]", " ", query)

    for disease in DISEASES:
        if re.search(r"\b" + re.escape(disease) + r"\b", normalized_query):
            concepts["diseases"].append(disease)

    for alias, canonical in ALIASES.items():
        if alias in normalized_query and canonical not in concepts["diseases"]:
            concepts["diseases"].append(canonical)

    for intent, words in INTENTS.items():
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", normalized_query):
                concepts["intent"] = intent
                break

        if concepts["intent"] != "general":
            break

    stop_words = {
        "what", "are", "the", "is", "of", "a", "an", "how", "can", "i", "me",
        "tell", "about", "please", "for", "and", "to", "give", "details", "info"
    }

    words = re.findall(r"\b[a-zA-Z]+\b", normalized_query)
    concepts["keywords"] = [
        word for word in words if word not in stop_words and len(word) > 2
    ]

    return concepts