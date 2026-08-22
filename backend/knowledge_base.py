import json
import os
import re

from medical_concepts import extract_medical_concepts


DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "health_data.json"
)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def load_health_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def search_health_data(query: str):
    data = load_health_data()
    concepts = extract_medical_concepts(query)
    normalized_query = normalize(query)

    matched_disease_keys = set(concepts.get("diseases", []))
    if not matched_disease_keys:
        return []

    candidate_keys = []
    for key, disease in data.items():
        searchable_text = " ".join([
            disease.get("name", ""),
            disease.get("category", ""),
            disease.get("transmission", ""),
            " ".join(disease.get("symptoms", [])),
            " ".join(disease.get("prevention", [])),
            " ".join(disease.get("warning_signs", [])),
            key,
        ]).lower()

        if key not in matched_disease_keys:
            continue

        score = 0
        query_tokens = set(normalized_query.split())
        searchable_tokens = set(searchable_text.split())

        if normalize(disease.get("name", "")) in normalized_query:
            score += 20

        if key in normalized_query or normalize(key) in normalized_query:
            score += 15

        for token in query_tokens:
            if token and token in searchable_tokens:
                score += 2

        if key in concepts.get("diseases", []) or any(item in normalized_query for item in [normalize(key), normalize(disease.get("name", ""))]):
            score += 10

        if score > 0:
            candidate_keys.append((key, score, searchable_text))

    if not candidate_keys:
        return []

    candidate_keys.sort(key=lambda item: item[1], reverse=True)
    results = []
    for key, score, _ in candidate_keys[:3]:
        disease = data[key]
        results.append({
            "disease": disease["name"],
            "information": disease,
            "score": score,
            "matched_concepts": concepts
        })

    return results