import re


DISEASES = [
    "dengue",
    "malaria",
    "influenza"
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


def extract_medical_concepts(query: str):
    query = query.lower()

    concepts = {
        "diseases": [],
        "intent": "general",
        "keywords": []
    }

    # Find disease concepts
    for disease in DISEASES:
        if re.search(r"\b" + re.escape(disease) + r"\b", query):
            concepts["diseases"].append(disease)

    # Find user intent
    for intent, words in INTENTS.items():
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", query):
                concepts["intent"] = intent
                break

        if concepts["intent"] != "general":
            break

    # Extract useful words
    stop_words = {
        "what",
        "are",
        "the",
        "is",
        "of",
        "a",
        "an",
        "how",
        "can",
        "i",
        "me",
        "tell",
        "about",
        "please",
        "for",
        "and",
        "to"
    }

    words = re.findall(r"\b[a-zA-Z]+\b", query)

    concepts["keywords"] = [
        word
        for word in words
        if word not in stop_words and len(word) > 2
    ]

    return concepts