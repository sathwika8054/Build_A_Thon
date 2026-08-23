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
4. Use the retrieved HealthGuard medical knowledge as the primary source when discussing specific database diseases.
5. If the user query is not covered by the retrieved database files, answer the question helpfuly and conversationally using your general pre-trained knowledge, keeping the advice educational and safe.
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

    if not answer or len(answer) < 5:
        from knowledge_base import search_health_data
        matches = search_health_data(user_query)
        if matches:
            first_match = matches[0]["information"]
            disease_name = first_match.get("name", "Unknown Disease")
            symptoms = ", ".join(first_match.get("symptoms", []))
            transmission = first_match.get("transmission", "N/A")
            prevention = "\n- " + "\n- ".join(first_match.get("prevention", []))
            warning_signs = ", ".join(first_match.get("warning_signs", []))
            
            if language == "telugu":
                return (
                    f"హెల్త్‌గార్డ్ నాలెడ్జ్ బేస్ ఆధారంగా **{disease_name}** సమాచారం ఇక్కడ ఉంది:\n\n"
                    f"🔴 **లక్షణాలు:** {symptoms}\n"
                    f"🔍 **వ్యాప్తి:** {transmission}\n"
                    f"🛡️ **నివారణ చర్యలు:** {prevention}\n"
                    f"⚠️ **హెచ్చరిక సంకేతాలు:** {warning_signs}\n\n"
                    f"వైద్య చికిత్స లేదా ఖచ్చితమైన రోగ నిర్ధారణ కోసం దయచేసి అర్హత కలిగిన ఆరోగ్య నిపుణుడిని సంప్రదించండి."
                )
            else:
                return (
                    f"Based on the HealthGuard knowledge base, here is the information for **{disease_name}**:\n\n"
                    f"🔴 **Symptoms:** {symptoms}\n"
                    f"🔍 **Transmission:** {transmission}\n"
                    f"🛡️ **Prevention:** {prevention}\n"
                    f"⚠️ **Warning Signs:** {warning_signs}\n\n"
                    f"Please consult a qualified healthcare professional for professional medical diagnosis and treatment."
                )
        
        if language == "telugu":
            return (
                "క్షమించండి, మీ ప్రశ్నకు సరిపోయే సమాచారం మా లోకల్ డేటాబేస్‌లో లభించలేదు.\n\n"
                "దయచేసి డెంగ్యూ, మలేరియా, టైఫాయిడ్, కోవిడ్-19, కలరా లేదా క్షయ (Tuberculosis) వంటి వ్యాధుల గురించి అడగండి.\n\n"
                "⚠️ వైద్య సలహా కోసం నిపుణుడిని సంప్రదించండి."
            )
        else:
            return (
                "I couldn't find a direct match for your specific query in our local database.\n\n"
                "However, we have detailed guidelines on Dengue, Malaria, Typhoid, COVID-19, Cholera, and Tuberculosis (TB). Please ask about these conditions to view recommendations.\n\n"
                "⚠️ Please consult a qualified healthcare professional for medical advice."
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
    # Define local pre-consultation helper for offline fallback
    def get_offline_consultation_response():
        user_turns = [turn for turn in (history or []) if turn.get("type") == "user"]
        turn_count = len(user_turns)
        
        searchable_text = (user_query + " " + " ".join([t.get("message", "") for t in (history or [])])).lower()
        
        disease_name = "your symptoms"
        if "dengue" in searchable_text:
            disease_name = "Dengue"
        elif "malaria" in searchable_text:
            disease_name = "Malaria"
        elif "typhoid" in searchable_text:
            disease_name = "Typhoid"
        elif "covid" in searchable_text:
            disease_name = "COVID-19"
        elif "cholera" in searchable_text:
            disease_name = "Cholera"
        elif "tuberculosis" in searchable_text or "tb" in searchable_text:
            disease_name = "Tuberculosis"

        if language == "telugu":
            if turn_count == 0:
                return "నమస్కారం! నేను మీ హెల్త్‌గార్డ్ కన్సల్టేషన్ అసిస్టెంట్‌ని. మీకు జ్వరం లేదా ఇతర లక్షణాలు ఎప్పటి నుండి ఉన్నాయి?"
            elif turn_count == 1:
                return f"ధన్యవాదాలు. మీకు {disease_name} కి సంబంధించిన జ్వరం కాకుండా ఒళ్లు నొప్పులు, వికారం లేదా తలనొప్పి వంటి ఇతర లక్షణాలు కూడా ఉన్నాయా?"
            elif turn_count == 2:
                return "మీకు తీవ్రమైన కడుపు నొప్పి, వాంతులు లేదా శ్వాస తీసుకోవడంలో ఇబ్బంది వంటి ఏవైనా తీవ్రమైన హెచ్చరిక సంకేతాలు ఉన్నాయా?"
            else:
                return (
                    f"సేకరించిన సమాచారం ప్రకారం: మీ లక్షణాలు {disease_name} తో సరిపోలవచ్చు.\n\n"
                    "సూచనలు:\n"
                    "1. తగినంత విశ్రాంతి తీసుకోండి మరియు ద్రవపదార్థాలు ఎక్కువగా తీసుకోండి.\n"
                    "2. దయచేసి ఖచ్చితమైన నిర్ధారణ మరియు చికిత్స కోసం ఒక వైద్యుడిని సంప్రదించండి.\n\n"
                    "⚠️ గమనిక: ఇది సాధారణ సమాచారం మాత్రమే, ఇది వైద్య సలహా కాదు."
                )
        else:
            if turn_count == 0:
                return "Hello! I am your HealthGuard pre-consultation assistant. Since when have you been experiencing these symptoms?"
            elif turn_count == 1:
                return f"Thank you. Along with the symptoms, do you have any other associated signs like headache, body aches, joint pain, or nausea?"
            elif turn_count == 2:
                return "Have you noticed any severe warning signs like persistent vomiting, extreme weakness, bleeding, or difficulty breathing?"
            else:
                return (
                    f"Based on the symptoms described, this may align with {disease_name}.\n\n"
                    "Educational Guidance:\n"
                    "- Rest well and stay fully hydrated.\n"
                    "- Please consult a healthcare professional for diagnosis and treatment.\n\n"
                    "⚠️ Notice: This information is for educational purposes and is not a medical diagnosis."
                )

    if not (OPENAI_API_KEY and client) or "your_openai_api" in OPENAI_API_KEY:
        return get_offline_consultation_response()

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
        print("Error in chatbot consultation generation (falling back to rule-based pre-consultation):", e)
        return get_offline_consultation_response()