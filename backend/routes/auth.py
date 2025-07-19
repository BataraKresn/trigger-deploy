from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from slowapi.util import get_remote_address
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
import logging

from utils.auth import hash_password, verify_password, generate_token, verify_token

load_dotenv()

router = APIRouter()

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Add middleware (if not already added in main app)
# app.add_middleware(SlowAPIMiddleware)

# ----------------------
# 🔒 User Auth Setup
# ----------------------
users_db = {}
for env_user, env_pass in [("ADMIN_USER", "ADMIN_PASS"), ("USER_USER", "USER_PASS")]:
    username = os.getenv(env_user)
    password = os.getenv(env_pass)
    if username and password:
        users_db[username] = hash_password(password)

if not users_db:
    raise RuntimeError("No valid user credentials found in environment variables.")

if not all([os.getenv("ADMIN_USER"), os.getenv("ADMIN_PASS"), os.getenv("USER_USER"), os.getenv("USER_PASS")]):
    logging.error("Missing required environment variables")
    raise RuntimeError("Missing required environment variables")

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)

class RefreshTokenRequest(BaseModel):
    token: str = Field(...)

@router.post("/api/login")
@limiter.limit("10/minute")  # optional: rate-limit login attempts
async def login(request: Request, payload: LoginRequest):
    logging.info(f"Login attempt for user: {payload.username} from IP: {request.client.host}")
    if payload.username in users_db and verify_password(payload.password, users_db[payload.username]):
        token = generate_token(payload.username)
        logging.info(f"Login successful for user: {payload.username}")
        return {"token": token}
    logging.warning(f"Login failed for user: {payload.username} from IP: {request.client.host}")
    raise HTTPException(status_code=401, detail="Invalid username or password")

@router.post("/api/refresh-token")
async def refresh_token(payload: RefreshTokenRequest, request: Request):
    username = verify_token(payload.token)
    if not username:
        logging.warning(f"Token refresh failed from IP: {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    new_token = generate_token(username)
    logging.info(f"Token refreshed for user: {username} from IP: {request.client.host}")
    return {"token": new_token}

# ----------------------
# 🚀 Password Validation (for Deploy UI)
# ----------------------

class PasswordPayload(BaseModel):
    password: str

@router.post("/api/validate-password")
@limiter.limit("5/minute")
async def validate_password(payload: PasswordPayload, request: Request):
    expected_password = os.getenv("DEPLOY_PASSWORD", "SAT2025")
    if payload.password == expected_password:
        return {"valid": True}
    raise HTTPException(status_code=401, detail="Invalid deploy password")

# ----------------------
# 📊 Dashboard Route (Token Protected)
# ----------------------

@router.get("/api/dashboard")
async def dashboard(request: Request):
    token = request.headers.get("Authorization")
    logging.debug(f"Received token: {token}")
    if not token or not token.startswith("Bearer ") or not verify_token(token.split("Bearer ")[1]):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {"message": "Welcome to the dashboard!"}

# ----------------------
# 🔑 Token Validation Endpoint
# ----------------------

@router.api_route("/api/validate-token", methods=["GET", "POST"])
async def validate_token(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer ") or not verify_token(token.split("Bearer ")[1]):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {"valid": True}
