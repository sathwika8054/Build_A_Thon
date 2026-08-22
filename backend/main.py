import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
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
# Request models
# --------------------------------

class ChatRequest(BaseModel):
    message: str
    image_data: str | None = None
    image_id: str | None = None
    context_disease: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


VALID_USERS = {
    "admin": "healthguard123",
    "doctor": "doctor123",
    "nurse": "nurse123"
}


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
# Login API
# --------------------------------

@app.post("/login")
def login(request: LoginRequest):
    username = (request.username or "").strip().lower()
    password = (request.password or "").strip()

    if username in VALID_USERS and VALID_USERS[username] == password:
        return {
            "success": True,
            "message": "Login successful",
            "username": username,
            "token": "demo-healthguard-token"
        }

    raise HTTPException(status_code=401, detail="Invalid username or password")


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


@app.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Please upload a JPG, PNG, WEBP, or GIF image")

    upload_directory = os.path.join(os.path.dirname(__file__), "data", "uploads")
    os.makedirs(upload_directory, exist_ok=True)
    extension = os.path.splitext(image.filename or "photo.jpg")[1].lower() or ".jpg"
    image_id = uuid.uuid4().hex
    file_path = os.path.join(upload_directory, f"{image_id}{extension}")
    content = await image.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")

    with open(file_path, "wb") as file:
        file.write(content)

    return {
        "success": True,
        "image_id": image_id,
        "filename": image.filename or "photo",
        "message": "Photo uploaded successfully"
    }


def is_follow_up_message(message: str) -> bool:
    words = set(message.lower().split())
    follow_up_words = {
        "since", "for", "days", "day", "weeks", "week", "today", "yesterday",
        "age", "old", "mild", "moderate", "severe", "yes", "no", "also", "and",
        "started", "duration", "pregnant", "medication", "medicine", "pain", "fever"
    }
    question_words = {"what", "why", "how", "when", "where", "who", "can", "should", "is"}
    return len(words) <= 12 and bool(words & follow_up_words) and not bool(words & question_words)


def conversational_answer(message: str) -> str:
    normalized = message.lower().strip()
    if normalized in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
        return "Hello. I am here to help with health questions. What would you like to know?"
    if "how are you" in normalized:
        return "I am ready to help. Tell me your question, symptoms, or the disease you want to understand."
    if "what can you do" in normalized or "who are you" in normalized:
        return "I can explain health conditions, symptoms, prevention, warning signs, and safer next steps. I will ask follow-up questions when more context is needed."
    if "thank" in normalized:
        return "You are welcome. Is there anything else about your health you would like to understand?"
    return (
        "I can answer that as a general health conversation, but I do not want to guess a diagnosis. "
        "Please tell me what you want to know and include any symptoms, how long they have been present, "
        "and how severe they are."
    )


# --------------------------------
# Chat API
# --------------------------------

@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    emergency_signs = check_emergency(user_message)
    concepts = extract_medical_concepts(user_message)
    use_context = not concepts.get("diseases") and request.context_disease and is_follow_up_message(user_message)
    search_message = " ".join(filter(None, [request.context_disease if use_context else None, user_message]))
    if use_context:
        concepts = extract_medical_concepts(search_message)
    related_concepts = get_related_concepts(concepts)
    health_information = search_health_data(search_message)

    if health_information:
        information_parts = []

        for item in health_information:
            disease_info = item.get("information", {}) or {}
            disease_name = item.get("disease") or disease_info.get("name", "related condition")
            category = disease_info.get("category", "General health")
            transmission = disease_info.get("transmission", "Not listed")
            symptoms = ", ".join(disease_info.get("symptoms", [])) or "Not listed"
            prevention = "; ".join(disease_info.get("prevention", [])) or "Follow general public-health guidance"
            warning = "; ".join(disease_info.get("warning_signs", [])) or "Seek professional care if symptoms are severe or worsening"

            information_parts.append(
                f"Medical information for {disease_name}:\n"
                f"Category: {category}\n"
                f"How it spreads or develops: {transmission}\n"
                f"Common symptoms: {symptoms}\n"
                f"Prevention: {prevention}\n"
                f"Warning signs: {warning}"
            )

        answer = "\n\n".join(information_parts)
    else:
        answer = conversational_answer(user_message)

    if emergency_signs:
        answer += (
            "\n\nIMPORTANT SAFETY ALERT:\n"
            "Your message contains possible emergency-related symptoms or situations.\n"
            "Please seek urgent professional medical attention when appropriate."
        )

    final_answer = add_safety_guidance(answer, health_information)

    follow_up = None
    if health_information and not any(word in user_message.lower() for word in [
        "when", "since", "days", "long", "age", "old", "pregnant", "medication"
    ]):
        follow_up = (
            "To understand your situation better: since when have you been experiencing "
            "these symptoms, and how severe are they right now?"
        )
        final_answer = final_answer.strip() + "\n\n" + follow_up

    if request.image_data or request.image_id:
        final_answer = (
            final_answer.strip() + "\n\nI received the uploaded image for context. "
            "I cannot diagnose an image, so please describe what you want checked and "
            "show it to a qualified clinician if it looks concerning."
        )

    return {
        "answer": final_answer,
        "medical_concepts": concepts,
        "related_concepts": related_concepts,
        "emergency_signs": emergency_signs,
        "sources_found": len(health_information),
        "disease_found": bool(health_information),
        "disease_details": health_information[0]["information"] if health_information else None,
        "follow_up": follow_up,
        "image_received": bool(request.image_data or request.image_id),
        "image_id": request.image_id
    }