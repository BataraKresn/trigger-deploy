import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_login_success():
    response = client.post("/login", json={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_failure():
    response = client.post("/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_login_rate_limit():
    for _ in range(11):
        response = client.post("/login", json={"username": "admin", "password": "password123"})
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
