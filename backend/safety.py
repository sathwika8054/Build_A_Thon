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


def add_safety_guidance(answer: str, medical_information: list):
    safety_message = """

⚠️ Health Information Notice:
This response provides general educational health information.
It is not a medical diagnosis and should not replace advice
from a qualified healthcare professional.

If your symptoms are severe, rapidly worsening, or you are
experiencing an emergency, seek immediate professional medical care.
"""

    return answer.strip() + "\n" + safety_message