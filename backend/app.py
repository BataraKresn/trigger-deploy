from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError

from loguru import logger
from decouple import config

from routes.deploy import router as deploy_router
from routes.logs import router as logs_router
from routes.health import router as health_router
from routes.auth import router as auth_router

from utils.rate_limit import limiter

# 
# Init FastAPI
app = FastAPI(
    title="Trigger Deploy API",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Logging Setup
logger.add("logs/backend_{time}.log", rotation="1 day", retention="7 days", level="INFO")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Validation error", "data": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail, "data": None}
    )

# Custom OpenAPI Schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Triggered Deployment API",
        version="1.0.0",
        description="API for managing deployments and authentication",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(deploy_router, prefix="/api/deploy", tags=["Deploy"])
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

@app.get("/api/status")
async def get_status():
    return {"status": "success", "message": "API is running", "data": None}