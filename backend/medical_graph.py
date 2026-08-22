# --------------------------------
# HealthGuard Medical Knowledge Graph
# --------------------------------

medical_graph = {

    "dengue": {
        "type": "disease",

        "symptoms": [
            "fever",
            "headache",
            "pain behind the eyes",
            "muscle pain",
            "joint pain",
            "nausea",
            "vomiting",
            "rash"
        ],

        "related_concepts": [
            "Aedes mosquito",
            "viral infection",
            "infectious disease"
        ]
    },

    "influenza": {
        "type": "disease",

        "symptoms": [
            "fever",
            "cough",
            "sore throat",
            "body aches",
            "headache",
            "fatigue"
        ],

        "related_concepts": [
            "respiratory infection",
            "respiratory droplets",
            "influenza virus"
        ]
    },

    "malaria": {
        "type": "disease",

        "symptoms": [
            "fever",
            "chills",
            "sweating",
            "headache",
            "body pain"
        ],

        "related_concepts": [
            "mosquito",
            "parasite",
            "infectious disease"
        ]
    },

    "diabetes": {
        "type": "disease",

        "symptoms": [
            "increased thirst",
            "frequent urination",
            "increased hunger",
            "fatigue"
        ],

        "related_concepts": [
            "blood sugar",
            "insulin",
            "metabolic disease"
        ]
    }
}


def get_related_concepts(concepts):

    results = []

    # --------------------------------
    # Extract diseases from
    # medical_concepts output
    # --------------------------------

    if isinstance(concepts, dict):

        diseases = concepts.get("diseases", [])

    else:

        diseases = concepts


    # --------------------------------
    # Find relationships
    # --------------------------------

    for disease in diseases:

        disease = disease.lower().strip()

        if disease in medical_graph:

            data = medical_graph[disease]

            results.append({

                "concept": disease,

                "type": data["type"],

                "symptoms": data["symptoms"],

                "related_concepts": data["related_concepts"]

            })


    return results