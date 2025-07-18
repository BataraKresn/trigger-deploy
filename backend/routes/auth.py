from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from routes.auth import router
from slowapi.util import get_remote_address
import os

from utils.auth import hash_password, verify_password, generate_token

load_dotenv()

router = APIRouter()

# ----------------------
# 🔐 User Auth Setup
# ----------------------
users_db = {}
for env_user, env_pass in [("ADMIN_USER", "ADMIN_PASS"), ("USER_USER", "USER_PASS")]:
    username = os.getenv(env_user)
    password = os.getenv(env_pass)
    if username and password:
        users_db[username] = hash_password(password)

if not users_db:
    raise RuntimeError("No valid user credentials found in environment variables.")

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)

@router.post("/login")
@limiter.limit("10/minute")  # optional: rate-limit login attempts
async def login(request: Request, payload: LoginRequest):
    if payload.username in users_db and verify_password(payload.password, users_db[payload.username]):
        return {"token": generate_token(payload.username)}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# ----------------------
# 🚀 Password Validation (for Deploy UI)
# ----------------------

class PasswordPayload(BaseModel):
    password: str

@router.post("/validate-password")
@limiter.limit("5/minute")
async def validate_password(payload: PasswordPayload, request: Request):
    expected_password = os.getenv("DEPLOY_PASSWORD", "SAT2025")
    if payload.password == expected_password:
        return {"valid": True}
    raise HTTPException(status_code=401, detail="Invalid deploy password")
