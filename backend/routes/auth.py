from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from utils.auth import hash_password, verify_password, generate_token

load_dotenv()

router = APIRouter()

# Load users from .env
users_db = {
    os.getenv("ADMIN_USER"): hash_password(os.getenv("ADMIN_PASS")),
    os.getenv("USER_USER"): hash_password(os.getenv("USER_PASS"))
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    if request.username in users_db and verify_password(request.password, users_db[request.username]):
        return {"token": generate_token(request.username)}
    raise HTTPException(status_code=401, detail="Invalid username or password")
