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
                "You are HealthGuard AI, a public-health "
                "assistant.\n\n"

                "Analyze the uploaded image and provide "
                "general educational health information.\n\n"

                "Do not provide a definitive medical diagnosis. "
                "Do not claim certainty about a disease or "
                "medical condition from an image alone.\n\n"

                "Describe visible observations when appropriate. "
                "Explain possible general health relevance. "
                "Recommend consulting a qualified healthcare "
                "professional when medical evaluation is needed.\n\n"

                "If the image is not medically relevant or "
                "cannot be interpreted reliably, clearly say so."
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