import os
import uuid

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends
)

from fastapi.responses import FileResponse

from pydantic import BaseModel

# --------------------------------
# Database
# --------------------------------

from database import (
    engine,
    Base,
    get_db
)

from models import User

# --------------------------------
# Authentication
# --------------------------------

import jwt

from pwdlib import PasswordHash

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

from ai_service import generate_health_response

# --------------------------------
# Image analysis
# --------------------------------

from image_service import analyze_medical_image


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


class LoginRequest(BaseModel):
    email: str
    password: str


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
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):

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
        password=hashed_password
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
        .filter(User.email == request.email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    try:

        valid_password = password_hash.verify(
            request.password,
            user.password
        )

    except Exception:

        valid_password = False

    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        user.id
    )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }


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
# CHAT ENDPOINT
# ================================================

@app.post("/chat")
def chat(
    request: ChatRequest
):

    # --------------------------------
    # Get user message
    # --------------------------------

    user_message = request.message.strip()

    if not user_message:

        return {
            "answer": "Please enter a health question.",
            "medical_concepts": {},
            "nlp_analysis": {},
            "related_concepts": [],
            "emergency_signs": [],
            "sources_found": 0
        }


    # --------------------------------
    # Emergency check
    # --------------------------------

    emergency_signs = check_emergency(
        user_message
    )


    # --------------------------------
    # Medical concept extraction
    # --------------------------------

    graph_concepts = extract_graph_concepts(
        user_message
    )


    # --------------------------------
    # Medical NLP
    # --------------------------------

    nlp_concepts = extract_nlp_concepts(
        user_message
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

    search_query = user_message

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

        user_query=user_message,

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

            rag_context=rag_context
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

    return {

        "answer": final_answer,

        "medical_concepts": graph_concepts,

        "nlp_analysis": nlp_concepts,

        "related_concepts": related_concepts,

        "emergency_signs": emergency_signs,

        "sources_found": len(
            health_information
        )
    }


# ================================================
# IMAGE UPLOAD + IMAGE ANALYSIS
# ================================================

@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...)
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

        if file.content_type not in allowed_types:

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
            file.filename
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

        contents = await file.read()


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
        # Return result
        # --------------------------------

        return {

            "success": True,

            "image_id": image_id,

            "filename": file.filename,

            "message": (
                "Photo uploaded and "
                "analyzed successfully"
            ),

            "analysis": analysis

        }


    except Exception as e:

        return {

            "success": False,

            "message": (
                "Image processing failed."
            ),

            "error": str(e)

        }