EMERGENCY_KEYWORDS = [
    "difficulty breathing",
    "chest pain",
    "severe bleeding",
    "unconscious",
    "loss of consciousness",
    "seizure",
    "cannot breathe",
    "suicidal"
]

def check_emergency(message: str):
    message = message.lower()

    detected = []

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message:
            detected.append(keyword)

    return detected


def add_safety_guidance(answer: str, medical_information: list, language: str = "english"):
    if language == "telugu":
        safety_message = """

⚠️ ఆరోగ్య సమాచార నోటీసు:
ఈ ప్రతిస్పందన సాధారణ విద్యా ఆరోగ్య సమాచారాన్ని అందిస్తుంది.
ఇది వైద్య నిర్ధారణ కాదు మరియు అర్హత కలిగిన ఆరోగ్య నిపుణుల సలహాను భర్తీ చేయకూడదు.

మీ లక్షణాలు తీవ్రంగా ఉంటే, వేగంగా క్షీణిస్తుంటే లేదా మీకు అత్యవసర పరిస్థితి ఎదురైతే, తక్షణమే వృత్తిపరమైన వైద్య సహాయాన్ని కోరండి.
"""
    else:
        safety_message = """

Health Information Notice:
This response provides general educational health information.
It is not a medical diagnosis and should not replace advice
from a qualified healthcare professional.

If your symptoms are severe, rapidly worsening, or you are
experiencing an emergency, seek immediate professional medical care.
"""

    return answer.strip() + "\n" + safety_message