import os
import base64

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# OPENAI CLIENT
# ============================================================

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key
)


# ============================================================
# SUPPORTED IMAGE TYPES
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
}


# ============================================================
# MAXIMUM IMAGE SIZE
# ============================================================

MAX_IMAGE_SIZE = 10 * 1024 * 1024


# ============================================================
# ANALYZE MEDICAL IMAGE
# ============================================================

def analyze_medical_image(
    image_bytes: bytes,
    content_type: str,
    user_question: str = ""
) -> str:

    # --------------------------------------------------------
    # Validate image type
    # --------------------------------------------------------

    if content_type not in ALLOWED_IMAGE_TYPES:

        raise ValueError(
            "Unsupported image type. "
            "Please upload JPG, JPEG, PNG, or WEBP."
        )


    # --------------------------------------------------------
    # Validate image size
    # --------------------------------------------------------

    if len(image_bytes) > MAX_IMAGE_SIZE:

        raise ValueError(
            "Image is too large. "
            "Maximum allowed size is 10 MB."
        )


    # --------------------------------------------------------
    # Convert image to Base64
    # --------------------------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # --------------------------------------------------------
    # Create data URL
    # --------------------------------------------------------

    image_data_url = (
        f"data:{content_type};base64,"
        f"{encoded_image}"
    )


    # --------------------------------------------------------
    # Medical safety instructions
    # --------------------------------------------------------

    system_instruction = """
You are HealthGuard AI, a public-health educational assistant.

Analyze the uploaded medical image carefully.

IMPORTANT SAFETY RULES:

1. Do not claim that an image provides a confirmed diagnosis.
2. Do not replace a doctor or qualified healthcare professional.
3. Describe only visible or reasonably inferable features.
4. Explain possible general medical interpretations when appropriate.
5. Clearly communicate uncertainty.
6. Do not recommend prescription medicines or dosages.
7. If the image appears potentially urgent, recommend appropriate
   professional medical evaluation.
8. Do not identify a person from an image.
9. Do not make claims that cannot reasonably be supported by the image.
10. If the image is unclear, say that it is unclear.
11. If the image is not medical or cannot be analyzed safely,
    explain that clearly.

Structure the response as:

OBSERVATIONS:
Describe what is visibly present.

POSSIBLE EXPLANATIONS:
Give general possibilities, not a confirmed diagnosis.

WHAT TO DO:
Give safe general next steps.

WHEN TO SEEK MEDICAL CARE:
Mention concerning signs that warrant professional evaluation.

DISCLAIMER:
State that image analysis is educational and cannot confirm
a medical diagnosis.
"""


    # --------------------------------------------------------
    # User question
    # --------------------------------------------------------

    if user_question.strip():

        user_text = (
            "The user uploaded a medical image.\n\n"
            "User question:\n"
            f"{user_question}\n\n"
            "Analyze the image in the context of this question."
        )

    else:

        user_text = (
            "The user uploaded a medical image.\n\n"
            "Analyze the image and provide a safe educational "
            "description of what can be observed."
        )


    # --------------------------------------------------------
    # OpenAI Vision request
    # --------------------------------------------------------

    response = client.responses.create(

        model="gpt-4.1-mini",

        instructions=system_instruction,

        input=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "input_text",

                        "text": user_text
                    },

                    {
                        "type": "input_image",

                        "image_url": image_data_url
                    }
                ]
            }
        ]
    )


    # --------------------------------------------------------
    # Get response text
    # --------------------------------------------------------

    return response.output_text