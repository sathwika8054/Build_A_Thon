import json
import os

from medical_concepts import extract_medical_concepts


DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "health_data.json"
)


def load_health_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def search_health_data(query: str):
    data = load_health_data()

    concepts = extract_medical_concepts(query)

    results = []

    for key, disease in data.items():

        score = 0

        # Disease concept match
        if key in concepts["diseases"]:
            score += 10

        # Keyword matching
        searchable_text = " ".join(
            [
                disease.get("name", ""),
                disease.get("category", ""),
                disease.get("transmission", ""),
                " ".join(disease.get("symptoms", [])),
                " ".join(disease.get("prevention", [])),
                " ".join(disease.get("warning_signs", []))
            ]
        ).lower()

        for keyword in concepts["keywords"]:
            if keyword in searchable_text:
                score += 1

        if score > 0:
            results.append({
                "disease": disease["name"],
                "information": disease,
                "score": score,
                "matched_concepts": concepts
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:3]