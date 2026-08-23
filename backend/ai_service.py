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
6. Keep explanations simple, conversational, and understandable.
7. If serious or emergency symptoms are present, recommend professional
   medical attention.
8. Do not replace advice from a qualified healthcare professional.
9. Always respond in the language specified in the user prompt (e.g., English or Telugu).
10. ALWAYS act like ChatGPT: keep the conversation interactive. At the end of every response, always ask the user 1 or 2 helpful follow-up questions related to their disease, symptoms, duration, or history to keep them talking and guide them safely.
"""


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def fallback_response(
    user_query: str,
    rag_context,
    language: str = "english"
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
        if language == "telugu":
            return (
                "ఈ ప్రశ్నకి సురక్షితంగా సమాధానం ఇవ్వడానికి హెల్త్‌గార్డ్ నాలెడ్జ్ బేస్‌లో తగినంత సమాచారం లభించలేదు.\n\n"
                "వైద్య సలహా కోసం దయచేసి అర్హత కలిగిన ఆరోగ్య నిపుణుడిని సంప్రదించండి.\n\n"
                "⚠️ ఈ సమాచారం సాధారణ విద్యా ప్రయోజనాల కోసం మాత్రమే మరియు ఇది వైద్య నిర్ధారణ కాదు."
            )
        else:
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

    if language == "telugu":
        return (
            "హెల్త్‌గార్డ్ నాలెడ్జ్ బేస్ ఆధారంగా:\n\n"
            f"{answer}\n\n"
            "⚠️ ఆరోగ్య సమాచార నోటీసు:\n"
            "ఈ ప్రతిస్పందన సాధారణ విద్యా సమాచారాన్ని మాత్రమే అందిస్తుంది. ఇది వైద్య నిర్ధారణ కాదు మరియు అర్హత కలిగిన ఆరోగ్య నిపుణుల సలహాను భర్తీ చేయకూడదు.\n\n"
            "మీ లక్షణాలు తీవ్రంగా ఉంటే, వేగంగా క్షీణిస్తుంటే లేదా మీకు అత్యవసర పరిస్థితి ఎదురైతే, తక్షణమే వృత్తిపరమైన వైద్య సంరక్షణను కోరండి."
        )
    else:
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
    rag_context,
    language: str = "english",
    history: list = None
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
            rag_context,
            language
        )


    # --------------------------------------------------------
    # Create AI prompt & messages list
    # --------------------------------------------------------

    input_messages = []

    if rag_context:
        input_messages.append({
            "role": "user",
            "content": f"Here is the retrieved HealthGuard medical information to ground our conversation:\n\n{rag_context}"
        })
        input_messages.append({
            "role": "assistant",
            "content": "Thank you. I will use this HealthGuard medical information as my primary source to answer your questions safely and concisely."
        })

    if history:
        for turn in history:
            role = "user" if turn.get("type") == "user" else "assistant"
            content = turn.get("message", "")
            if content:
                input_messages.append({
                    "role": role,
                    "content": content
                })

    prompt = f"""
User question:

{user_query}


Answer the user's question in the {language} language using the retrieved
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
- IMPORTANT: You MUST generate your entire response in the {language} language. If the selected language is 'telugu', you must write your response in the Telugu script (తెలుగు).
"""

    input_messages.append({
        "role": "user",
        "content": prompt
    })


    # --------------------------------------------------------
    # Call OpenAI
    # --------------------------------------------------------

    try:

        response = client.responses.create(

            model="gpt-4.1-mini",

            instructions=SYSTEM_INSTRUCTION,

            input=input_messages
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
                rag_context,
                language
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
            rag_context,
            language
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
            rag_context,
            language
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
            rag_context,
            language
        )


    except Exception as error:

        print(
            f"WARNING: Unexpected AI error: {error}"
        )

        return fallback_response(
            user_query,
            rag_context,
            language
        )


# ============================================================
# CHATBOT MEDICAL CONSULTATION INSTRUCTIONS
# ============================================================

CHATBOT_CONSULTATION_INSTRUCTION = """
You are a helpful, professional clinical pre-consultation chatbot acting like a doctor performing an initial consultation.

Your goal is to interview the user about their health concerns and symptoms step-by-step.

IMPORTANT CONVERSATIONAL RULES:
1. Ask exactly ONE medically relevant follow-up question at a time. Do NOT list multiple questions at once.
2. Proactively follow up on symptoms mentioned (e.g., if they have a fever, ask: "Since when have you had the fever?", then: "What is your temperature?", then: "Do you have chills, sore throat, or body pain?").
3. Do not rush to give advice. Keep asking intelligent, relevant follow-up questions one by one until you have collected sufficient information (at least 3-4 turns of questions if symptoms are described).
4. Once you have collected enough information, summarize all the collected symptoms clearly before offering general educational guidance.

SAFETY RULES:
- Never diagnose any disease or state a final diagnosis.
- Never prescribe any medications or suggest specific dosages.
- Recommend consulting a healthcare professional, especially if symptoms are serious.
- Explain all medical information in simple, clear, layperson language.
- Always respond in the language requested by the user (English or Telugu script).
"""

def generate_chatbot_consultation_response(
    user_query: str,
    history: list = None,
    language: str = "english",
    rag_context: str = None
):
    if not (OPENAI_API_KEY and client):
        if language == "telugu":
            return (
                "ఈ ప్రతిస్పందనను విజయవంతంగా పూర్తి చేయడానికి తగినంత సర్వర్ కనెక్టివిటీ సమాచారం లభించలేదు.\n\n"
                "వైద్య సలహా కోసం దయచేసి అర్హత కలిగిన ఆరోగ్య నిపుణుడిని సంప్రదించండి."
            )
        else:
            return (
                "I'm sorry, I cannot perform the clinical consultation right now due to server configuration issues.\n\n"
                "Please consult a qualified healthcare professional for medical advice."
            )

    input_messages = []

    if rag_context:
        input_messages.append({
            "role": "system",
            "content": f"Use the following HealthGuard medical database knowledge to ground your consultation questions and final summary advice. Do not mention the word 'database' or 'RAG' to the user:\n\n{rag_context}"
        })

    if history:
        for turn in history:
            role = "user" if turn.get("type") == "user" else "assistant"
            content = turn.get("message", "")
            if content:
                input_messages.append({
                    "role": role,
                    "content": content
                })

    prompt = f"""
User response:
{user_query}

Respond in the {language} language. Follow the clinical instruction strictly. Ask only one question at a time.
"""
    input_messages.append({
        "role": "user",
        "content": prompt
    })

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=CHATBOT_CONSULTATION_INSTRUCTION,
            input=input_messages
        )
        return response.output_text
    except Exception as e:
        print("Error in chatbot consultation generation:", e)
        if language == "telugu":
            return "క్షమించండి, మీ అభ్యర్థనను ప్రాసెస్ చేయడంలో లోపం సంభవించింది."
        else:
            return "Sorry, an error occurred while processing your request."