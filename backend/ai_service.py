import os

from dotenv import load_dotenv
from openai import (
    OpenAI,
    RateLimitError,
    APIError,
    APIConnectionError
)

load_dotenv()


# ============================================================
# OPENAI CONFIGURATION
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None

if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are HealthGuard AI, a public-health information assistant.

Your purpose is to provide safe, general educational health information.

IMPORTANT RULES:

1. Do not diagnose the user.
2. Do not prescribe medicines.
3. Do not invent medical information.
4. Use the retrieved HealthGuard medical knowledge as the primary source.
5. If the retrieved information is insufficient, clearly say so.
6. Keep explanations simple and understandable.
7. If serious or emergency symptoms are present, recommend professional
   medical attention.
8. Do not replace advice from a qualified healthcare professional.
"""


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def fallback_response(
    user_query: str,
    rag_context
):

    # --------------------------------------------------------
    # Convert RAG context into text
    # --------------------------------------------------------

    if rag_context is None:

        context_text = ""

    elif isinstance(rag_context, str):

        context_text = rag_context

    else:

        context_text = str(rag_context)


    # --------------------------------------------------------
    # Find trusted medical knowledge
    # --------------------------------------------------------

    answer = ""

    if "TRUSTED MEDICAL KNOWLEDGE:" in context_text:

        answer = context_text.split(
            "TRUSTED MEDICAL KNOWLEDGE:",
            1
        )[1]

        # Remove the medical knowledge graph section
        if "MEDICAL KNOWLEDGE GRAPH:" in answer:

            answer = answer.split(
                "MEDICAL KNOWLEDGE GRAPH:",
                1
            )[0]

        answer = answer.strip()

    else:

        answer = context_text.strip()


    # --------------------------------------------------------
    # If RAG returned nothing
    # --------------------------------------------------------

    if not answer:

        return (
            "I could not find enough relevant information "
            "in the HealthGuard knowledge base to answer "
            "this question safely.\n\n"
            "Please consult a qualified healthcare professional "
            "for medical advice.\n\n"
            "⚠️ This information is for general educational "
            "purposes and is not a medical diagnosis."
        )


    # --------------------------------------------------------
    # Clean common dictionary formatting
    # --------------------------------------------------------

    answer = answer.replace(
        "Information:\n",
        ""
    )

    answer = answer.replace(
        "{'name': 'Dengue',",
        "Dengue information:\n"
    )


    # --------------------------------------------------------
    # Remove unwanted internal sections
    # --------------------------------------------------------

    if "USER QUESTION:" in answer:

        answer = answer.split(
            "USER QUESTION:",
            1
        )[0].strip()


    if "MEDICAL NLP ANALYSIS:" in answer:

        answer = answer.split(
            "MEDICAL NLP ANALYSIS:",
            1
        )[0].strip()


    # --------------------------------------------------------
    # Final fallback response
    # --------------------------------------------------------

    return (
        "Based on the HealthGuard knowledge base:\n\n"
        f"{answer}\n\n"
        "⚠️ Health Information Notice:\n"
        "This response provides general educational health "
        "information. It is not a medical diagnosis and should "
        "not replace advice from a qualified healthcare professional.\n\n"
        "If your symptoms are severe, rapidly worsening, or you "
        "are experiencing an emergency, seek professional medical care."
    )


# ============================================================
# GENERATE HEALTH RESPONSE
# ============================================================

def generate_health_response(
    user_query: str,
    rag_context
):

    # --------------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------------

    print()
    print("================================================")
    print("              HEALTHGUARD AI")
    print("================================================")

    print("USER QUESTION:")
    print(user_query)

    print()
    print("RAG CONTEXT:")
    print(rag_context)

    print()
    print("================================================")


    # --------------------------------------------------------
    # Check OpenAI API key
    # --------------------------------------------------------

    if not OPENAI_API_KEY:

        print(
            "WARNING: OPENAI_API_KEY is missing."
        )

        return fallback_response(
            user_query,
            rag_context
        )


    # --------------------------------------------------------
    # Create AI prompt
    # --------------------------------------------------------

    prompt = f"""
User question:

{user_query}


Retrieved HealthGuard medical information:

{rag_context}


Answer the user's question using the retrieved
HealthGuard information.

Requirements:

- Do not diagnose the user.
- Do not prescribe medication.
- Do not invent medical information.
- Use the retrieved information as the primary source.
- If the retrieved information is insufficient,
  clearly say so.
- Keep the answer concise and understandable.
- Include appropriate safety guidance.
"""


    # --------------------------------------------------------
    # Call OpenAI
    # --------------------------------------------------------

    try:

        response = client.responses.create(

            model="gpt-4.1-mini",

            instructions=SYSTEM_INSTRUCTION,

            input=prompt
        )


        # ----------------------------------------------------
        # Get generated answer
        # ----------------------------------------------------

        answer = response.output_text


        # ----------------------------------------------------
        # Check empty response
        # ----------------------------------------------------

        if not answer or not answer.strip():

            print(
                "WARNING: OpenAI returned an empty response."
            )

            return fallback_response(
                user_query,
                rag_context
            )


        print(
            "OpenAI response generated successfully."
        )


        return answer


    # --------------------------------------------------------
    # OpenAI quota error
    # --------------------------------------------------------

    except RateLimitError:

        print(
            "WARNING: OpenAI API quota is exhausted."
        )

        return fallback_response(
            user_query,
            rag_context
        )


    # --------------------------------------------------------
    # OpenAI connection error
    # --------------------------------------------------------

    except APIConnectionError:

        print(
            "WARNING: Could not connect to OpenAI API."
        )

        return fallback_response(
            user_query,
            rag_context
        )


    # --------------------------------------------------------
    # Other OpenAI API errors
    # --------------------------------------------------------

    except APIError as error:

        print(
            f"WARNING: OpenAI API error: {error}"
        )

        return fallback_response(
            user_query,
            rag_context
        )


    # --------------------------------------------------------
    # Unexpected error
    # --------------------------------------------------------

    except Exception as error:

        print(
            f"WARNING: Unexpected AI error: {error}"
        )

        return fallback_response(
            user_query,
            rag_context
        )