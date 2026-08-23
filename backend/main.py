import os
import uuid

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Header
)

from fastapi.responses import FileResponse

from pydantic import BaseModel
from schemas import RegisterRequest

# --------------------------------
# Database
# --------------------------------

from database import (
    engine,
    Base,
    get_db
)

from models import User, ChatHistory

# --------------------------------
# Authentication
# --------------------------------

import jwt

from pwdlib import PasswordHash

from sqlalchemy import or_
from sqlalchemy.orm import Session

# --------------------------------
# Existing HealthGuard modules
# --------------------------------

from knowledge_base import search_health_data

from medical_concepts import (
    extract_medical_concepts as extract_graph_concepts
)

from medical_graph import get_related_concepts

from safety import (
    check_emergency,
    add_safety_guidance
)

from medical_nlp import (
    extract_medical_concepts as extract_nlp_concepts
)

from rag import build_rag_context

from ai_service import (
    generate_health_response,
    generate_chatbot_consultation_response
)

# --------------------------------
# Image analysis
# --------------------------------

from image_service import analyze_medical_image


# ================================================
# TRANSLATION HELPER FOR DISEASE DETAILS
# ================================================

def translate_disease_details_to_telugu(details: dict) -> dict:
    from ai_service import client, OPENAI_API_KEY
    if not (OPENAI_API_KEY and client) or not details:
        return details
    
    try:
        import json
        payload_to_translate = {
            "name": details.get("name", ""),
            "category": details.get("category", ""),
            "transmission": details.get("transmission", ""),
            "symptoms": details.get("symptoms", []),
            "prevention": details.get("prevention", []),
            "warning_signs": details.get("warning_signs", [])
        }
        
        prompt = f"""
Translate the following JSON values from English to Telugu script.
Keep key names exactly identical. Ensure translation is medical/clinical quality.
Return only the translated JSON block, no markdown code block formatting, no other explanation text.

{json.dumps(payload_to_translate)}
"""
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions="You are a medical translator translating English health statistics and descriptions to Telugu script.",
            input=prompt
        )
        translated_json = response.output_text.strip()
        
        if "```json" in translated_json:
            translated_json = translated_json.split("```json")[1].split("```")[0].strip()
        elif "```" in translated_json:
            translated_json = translated_json.split("```")[1].split("```")[0].strip()
            
        translated_data = json.loads(translated_json)
        
        new_details = details.copy()
        new_details.update(translated_data)
        return new_details
    except Exception as e:
        print("Error translating disease details to Telugu:", e)
        return details


# ================================================
# LOAD ENVIRONMENT VARIABLES
# ================================================

load_dotenv()


# ================================================
# DATABASE INITIALIZATION
# ================================================

try:
    Base.metadata.create_all(
        bind=engine
    )
except Exception as e:
    print("Database initialization warning:", e)


# ================================================
# FASTAPI APPLICATION
# ================================================

app = FastAPI(
    title="HealthGuard AI",
    description="AI-powered Public Health Assistant",
    version="1.0.0"
)


# ================================================
# PASSWORD HASHING
# ================================================

password_hash = PasswordHash.recommended()


# ================================================
# JWT SETTINGS
# ================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "healthguard-development-secret-key"
)

ALGORITHM = "HS256"


# ================================================
# REQUEST MODELS
# ================================================

class ChatRequest(BaseModel):
    message: str
    image_id: str | None = None
    image_data: str | None = None
    language: str | None = "english"
    history: list | None = None


class ChatbotRequest(BaseModel):
    message: str
    language: str | None = "english"
    history: list | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    username: str
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    username: str
    email: str
    new_password: str


# ================================================
# ROOT ENDPOINT
# ================================================

@app.get("/")
def home():

    return {
        "message": "HealthGuard AI is running!",
        "status": "healthy"
    }


# ================================================
# HEALTHGUARD WEB APP
# ================================================

@app.get("/app")
def healthguard_app():

    file_path = os.path.join(
        os.path.dirname(__file__),
        "index.html"
    )

    if not os.path.exists(file_path):

        raise HTTPException(
            status_code=404,
            detail="index.html not found"
        )

    return FileResponse(file_path)


# ================================================
# REGISTER
# ================================================

@app.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    username = request.username.strip()
    email = str(request.email).strip().lower()
    password = request.password

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Check whether email already exists

    existing_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check username

    existing_username = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Hash password

    hashed_password = password_hash.hash(
        password
    )

    # Create user

    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return {
        "success": True,
        "message": "Registration successful",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }


# ================================================
# CREATE JWT TOKEN
# ================================================

def create_access_token(
    user_id: int
):

    payload = {
        "user_id": user_id
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# ================================================
# LOGIN
# ================================================

@app.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            or_(
                User.username == request.username.strip(),
                User.email == request.username.strip()
            )
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    try:

        valid_password = password_hash.verify(
            request.password,
            user.hashed_password
        )

    except Exception:

        valid_password = False

    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(
        user.id
    )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }


@app.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(
            or_(
                User.username == request.username.strip(),
                User.email == request.username.strip()
            )
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        current_password_valid = password_hash.verify(
            request.current_password,
            user.hashed_password
        )
    except Exception:
        current_password_valid = False

    if not current_password_valid:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    if request.new_password == request.current_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    user.hashed_password = password_hash.hash(request.new_password)
    db.commit()
    return {"success": True, "message": "Password changed successfully"}


@app.post("/reset-password")
def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(
            (User.username == request.username.strip()) |
            (User.email == request.username.strip())
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email.lower() != request.email.strip().lower():
        raise HTTPException(status_code=400, detail="Invalid registered email address")

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user.hashed_password = password_hash.hash(request.new_password)
    db.commit()
    return {"success": True, "message": "Password reset successfully. You can now log in."}


# ================================================
# GET CURRENT USER
# ================================================

def get_current_user(
    token: str,
    db: Session
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get(
            "user_id"
        )

        if not user_id:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except jwt.PyJWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# ================================================
# ME ENDPOINT
# ================================================

@app.get("/me")
def me(
    token: str,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        token,
        db
    )

    return {
        "success": True,
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }


# ================================================
# LOGOUT ENDPOINT
# ================================================

@app.post("/logout")
def logout():
    return {
        "success": True,
        "message": "Logged out successfully"
    }


# ================================================
# CHAT ENDPOINT
# ================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):

    # --------------------------------
    # Get user message
    # --------------------------------

    user_message = request.message.strip()
    language = request.language or "english"

    if not user_message:

        return {
            "answer": "Please enter a health question.",
            "medical_concepts": {},
            "nlp_analysis": {},
            "related_concepts": [],
            "emergency_signs": [],
            "sources_found": 0
        }

    # Translate Telugu to English for concept matching and data searching
    processed_message = user_message
    if language == "telugu":
        from ai_service import OPENAI_API_KEY, client
        if OPENAI_API_KEY and client:
            try:
                translation_response = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions="You are a translation assistant. Translate the user query from Telugu to English. Output only the translated English text, nothing else.",
                    input=f"Translate: {user_message}"
                )
                translated_text = translation_response.output_text.strip()
                if translated_text:
                    processed_message = translated_text
            except Exception as e:
                print("Translation error in /chat:", e)

    # --------------------------------
    # Emergency check
    # --------------------------------

    emergency_signs = check_emergency(
        processed_message
    )


    # --------------------------------
    # Medical concept extraction
    # --------------------------------

    graph_concepts = extract_graph_concepts(
        processed_message
    )


    # --------------------------------
    # Medical NLP
    # --------------------------------

    nlp_concepts = extract_nlp_concepts(
        processed_message
    )


    # --------------------------------
    # Knowledge graph
    # --------------------------------

    related_concepts = get_related_concepts(
        graph_concepts
    )


    # --------------------------------
    # Search knowledge base
    # --------------------------------

    search_query = processed_message

    if isinstance(
        nlp_concepts,
        dict
    ):

        detected_disease = (
            nlp_concepts.get("disease")
        )

        if detected_disease:

            search_query = detected_disease


    health_information = search_health_data(
        search_query
    )


    # --------------------------------
    # RAG
    # --------------------------------

    rag_context = build_rag_context(

        user_query=processed_message,

        nlp_analysis=nlp_concepts,

        health_information=health_information,

        related_concepts=related_concepts
    )


    # --------------------------------
    # AI response
    # --------------------------------

    if health_information:

        answer = generate_health_response(

            user_query=user_message,

            rag_context=rag_context,

            language=language,

            history=request.history
        )

    else:

        answer = (
            "I could not find enough relevant "
            "information in the current HealthGuard "
            "public-health knowledge base to answer "
            "this safely."
        )


    # --------------------------------
    # Emergency guidance
    # --------------------------------

    if emergency_signs:

        answer += (

            "\n\n⚠️ IMPORTANT SAFETY ALERT:\n"

            "Your message contains possible "
            "emergency-related symptoms or situations.\n"

            "Please seek urgent professional "
            "medical attention when appropriate."
        )


    # --------------------------------
    # Safety guidance
    # --------------------------------

    final_answer = add_safety_guidance(
        answer,
        health_information
    )


    # --------------------------------
    # Final response
    # --------------------------------

    disease_details = None
    if health_information:
        disease_details = health_information[0]["information"]
        if language == "telugu":
            disease_details = translate_disease_details_to_telugu(disease_details)

    # --------------------------------
    # Save chat history to database (if authenticated user)
    # --------------------------------

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                chat_record = ChatHistory(
                    user_id=user_id,
                    question=user_message,
                    answer=final_answer
                )
                db.add(chat_record)
                db.commit()
        except Exception as db_err:
            print("Failed to save chat history to database:", db_err)

    return {

        "answer": final_answer,

        "medical_concepts": graph_concepts,

        "nlp_analysis": nlp_concepts,

        "related_concepts": related_concepts,

        "emergency_signs": emergency_signs,

        "sources_found": len(
            health_information
        ),

        "disease_details": disease_details
    }


# ================================================
# IMAGE UPLOAD + IMAGE ANALYSIS
# ================================================

@app.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...)
):

    try:

        # --------------------------------
        # Allowed image types
        # --------------------------------

        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp"
        }

        if image.content_type not in allowed_types:

            return {
                "success": False,
                "message": (
                    "Only JPG, PNG and WEBP "
                    "images are supported."
                )
            }


        # --------------------------------
        # Upload directory
        # --------------------------------

        upload_dir = os.path.join(
            os.path.dirname(__file__),
            "uploads"
        )

        os.makedirs(
            upload_dir,
            exist_ok=True
        )


        # --------------------------------
        # Unique image ID
        # --------------------------------

        image_id = uuid.uuid4().hex


        # --------------------------------
        # File extension
        # --------------------------------

        extension = os.path.splitext(
            image.filename
        )[1].lower()


        # --------------------------------
        # Image path
        # --------------------------------

        image_path = os.path.join(
            upload_dir,
            image_id + extension
        )


        # --------------------------------
        # Read uploaded image
        # --------------------------------

        contents = await image.read(5 * 1024 * 1024 + 1)

        if len(contents) > 5 * 1024 * 1024:
            return {
                "success": False,
                "message": "Image must be 5 MB or smaller."
            }


        # --------------------------------
        # Save image
        # --------------------------------

        with open(
            image_path,
            "wb"
        ) as image_file:

            image_file.write(contents)


        # --------------------------------
        # Analyze image
        # --------------------------------

        analysis = analyze_medical_image(
            image_path
        )


        # --------------------------------
        # Extract concepts & disease details
        # --------------------------------

        concepts = extract_graph_concepts(analysis)
        emergency_signs = check_emergency(analysis)

        active_disease = None
        disease_details = None

        if concepts.get("diseases"):
            active_disease = concepts["diseases"][0]
            health_info = search_health_data(active_disease)
            if health_info:
                disease_details = health_info[0]["information"]


        # --------------------------------
        # Return result
        # --------------------------------

        return {

            "success": True,

            "image_id": image_id,

            "filename": image.filename,

            "message": (
                "Photo uploaded and "
                "analyzed successfully"
            ),

            "analysis": analysis,

            "active_disease": active_disease,

            "disease_details": disease_details,

            "medical_concepts": concepts,

            "emergency_signs": emergency_signs

        }


    except Exception as e:

        return {

            "success": False,

            "message": (
                "Image processing failed."
            ),

            "error": str(e)

        }


# ================================================
# CHAT HISTORY ENDPOINT
# ================================================

@app.get("/chat-history")
def get_user_chat_history(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).limit(20).all()
    
    return [
        {
            "id": item.id,
            "question": item.question,
            "answer": item.answer,
            "created_at": item.created_at.isoformat()
        } for item in history
    ]


# ================================================
# CLINICAL CHATBOT CONSULTATION ENDPOINT
# ================================================

@app.post("/chatbot")
def chatbot(
    request: ChatbotRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    user_message = request.message.strip()
    language = request.language or "english"

    if not user_message:
        return {"answer": "Please enter a health question or symptom."}

    # Translate Telugu user message to English for backend checks if needed
    processed_message = user_message
    if language == "telugu":
        from ai_service import OPENAI_API_KEY, client
        if OPENAI_API_KEY and client:
            try:
                translation_response = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions="You are a translation assistant. Translate the user query from Telugu to English. Output only the translated English text, nothing else.",
                    input=f"Translate: {user_message}"
                )
                translated_text = translation_response.output_text.strip()
                if translated_text:
                    processed_message = translated_text
            except Exception as e:
                print("Translation error in /chatbot:", e)

    # Build RAG context from pre-consultation search
    health_information = search_health_data(processed_message)
    rag_context = ""
    if health_information:
        rag_context = build_rag_context(
            user_query=processed_message,
            nlp_analysis=extract_nlp_concepts(processed_message),
            health_information=health_information,
            related_concepts=get_related_concepts(extract_graph_concepts(processed_message))
        )

    # Generate chatbot medical consultation response
    answer = generate_chatbot_consultation_response(
        user_query=user_message,
        history=request.history,
        language=language,
        rag_context=rag_context
    )

    # Save to chat history table if authenticated
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                chat_record = ChatHistory(
                    user_id=user_id,
                    question=user_message,
                    answer=answer
                )
                db.add(chat_record)
                db.commit()
        except Exception as db_err:
            print("Failed to save chatbot history to database:", db_err)

    return {
        "answer": answer
    }