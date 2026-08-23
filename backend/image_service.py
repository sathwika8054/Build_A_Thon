import os
import base64

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def analyze_medical_image(image_path: str) -> str:
    """
    Analyze an uploaded medical-related image.

    This provides general educational information.
    It does not provide a medical diagnosis.
    """

    try:

        # Check that the image exists
        if not os.path.exists(image_path):
            return "The uploaded image could not be found."

        # Read image
        with open(image_path, "rb") as image_file:

            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        # Determine image type
        extension = os.path.splitext(
            image_path
        )[1].lower()

        if extension in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"

        elif extension == ".png":
            mime_type = "image/png"

        elif extension == ".webp":
            mime_type = "image/webp"

        else:
            return (
                "Unsupported image format. "
                "Please upload JPG, PNG, or WEBP."
            )

        if client is None:
            return (
                "The image was uploaded successfully, but AI image analysis "
                "needs an OPENAI_API_KEY configuration."
            )

        # Send image to OpenAI
        response = client.responses.create(

            model="gpt-4.1-mini",

            instructions=(
                "You are HealthGuard AI, a public-health assistant.\n\n"

                "Analyze the uploaded image. Check if it is a medical document such as a health report, lab test report (e.g., blood test, urine test, radiology report), or a doctor's prescription note.\n\n"

                "If it is a medical document (health report, lab test, or prescription note):\n"
                "1. Identify the health disease or condition mentioned, diagnosed, or indicated in the report.\n"
                "2. Extract and list the prescription details (e.g., prescribed medications, dosage, frequency, duration, and instructions) given in the report.\n"
                "3. Summarize key findings or observations from the report.\n"
                "4. Provide general, safe public health educational information about the identified disease or condition.\n"
                "Please structure your response clearly using the following markdown headers:\n"
                "- **Document Type**: (e.g., Blood Test, Prescription Note, Clinical Summary)\n"
                "- **Identified Condition/Disease**: (List the diseases/conditions explicitly mentioned or indicated)\n"
                "- **Prescription & Medications**: (List the medications, dosage, frequency, and instructions written on the document)\n"
                "- **Key Findings/Observations**: (Summary of test metrics or clinical observations)\n"
                "- **General Educational Insights**: (Safe educational explanations of the condition and standard care advice)\n\n"

                "If it is NOT a medical document but a photo of a symptom (e.g., skin rash, throat, eye irritation):\n"
                "1. Describe visible observations when appropriate.\n"
                "2. Explain possible general health relevance.\n"
                "3. Recommend consulting a qualified healthcare professional.\n\n"

                "Do not provide a new definitive medical diagnosis on your own. If the document has a diagnosis or prescription, you are only extracting and explaining it. Do not claim certainty about a disease from a symptom photo alone.\n\n"

                "If the image is not medically relevant or cannot be interpreted reliably, clearly say so."
            ),

            input=[
                {
                    "role": "user",
                    "content": [

                        {
                            "type": "input_text",
                            "text": (
                                "Please analyze this image and "
                                "provide general educational "
                                "health information."
                            )
                        },

                        {
                            "type": "input_image",
                            "image_url": (
                                f"data:{mime_type};base64,"
                                f"{image_data}"
                            )
                        }

                    ]
                }
            ]
        )

        return response.output_text

    except Exception as e:

        error_message = str(e)

        # OpenAI quota error
        if "insufficient_quota" in error_message:
            return (
                "Image uploaded successfully, but AI image "
                "analysis is currently unavailable because "
                "the OpenAI API has no remaining credits."
            )

        # Rate-limit error
        if "RateLimitError" in error_message:
            return (
                "Image uploaded successfully, but the AI "
                "analysis service is temporarily unavailable."
            )

        # General error
        return (
            "The image was uploaded successfully, but "
            "image analysis could not be completed."
        )