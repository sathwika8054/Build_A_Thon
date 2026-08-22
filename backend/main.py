import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from knowledge_base import search_health_data
from medical_concepts import extract_medical_concepts
from medical_graph import get_related_concepts
from safety import check_emergency, add_safety_guidance


# --------------------------------
# Load environment variables
# --------------------------------

load_dotenv()


# --------------------------------
# Create FastAPI application
# --------------------------------

app = FastAPI(
    title="HealthGuard AI",
    description="AI-powered Public Health Assistant",
    version="1.0.0"
)


# --------------------------------
# Request model
# --------------------------------

class ChatRequest(BaseModel):
    message: str


# --------------------------------
# Home API
# --------------------------------

@app.get("/")
def home():
    return {
        "message": "HealthGuard AI is running!",
        "status": "healthy"
    }


# --------------------------------
# HealthGuard AI Web App
# --------------------------------

@app.get("/app")
def healthguard_app():

    file_path = os.path.join(
        os.path.dirname(__file__),
        "index.html"
    )

    return FileResponse(file_path)


# --------------------------------
# Chat API
# --------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    # Get user message
    user_message = request.message.strip()


    # --------------------------------
    # 1. Check emergency keywords
    # --------------------------------

    emergency_signs = check_emergency(user_message)


    # --------------------------------
    # 2. Extract medical concepts
    # --------------------------------

    concepts = extract_medical_concepts(user_message)


    # --------------------------------
    # 3. Find related concepts
    #    using Medical Knowledge Graph
    # --------------------------------

    related_concepts = get_related_concepts(concepts)


    # --------------------------------
    # 4. Search medical knowledge base
    # --------------------------------

    health_information = search_health_data(user_message)


    # --------------------------------
    # 5. Build answer
    # --------------------------------

    if health_information:

        information_parts = []

        for item in health_information:

            information_parts.append(
                f"Medical information for {item['disease']}:\n"
                f"{item['information']}"
            )

        answer = "\n\n".join(information_parts)

    else:

        answer = (
            "I could not find relevant information in the current "
            "HealthGuard public-health knowledge base."
        )


    # --------------------------------
    # 6. Emergency guidance
    # --------------------------------

    if emergency_signs:

        answer += (
            "\n\nIMPORTANT SAFETY ALERT:\n"
            "Your message contains possible emergency-related "
            "symptoms or situations.\n"
            "Please seek urgent professional medical attention "
            "when appropriate."
        )


    # --------------------------------
    # 7. Add safety guidance
    # --------------------------------

    final_answer = add_safety_guidance(
        answer,
        health_information
    )


    # --------------------------------
    # 8. Return final response
    # --------------------------------

    return {

        "answer": final_answer,

        "medical_concepts": concepts,

        "related_concepts": related_concepts,

        "emergency_signs": emergency_signs,

        "sources_found": len(health_information)

    }