from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from loguru import logger
from decouple import config

from routes.deploy import router as deploy_router
from routes.logs import router as logs_router
from routes.health import router as health_router
from routes.auth import router as auth_router

from utils.rate_limit import limiter

# ✅ Init FastAPI
app = FastAPI(
    title="Trigger Deploy API",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ---------------------------
# 🪵 Logging Setup
# ---------------------------
logger.add("logs/backend_{time}.log", rotation="1 day", retention="7 days", level="INFO")

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# ---------------------------
# 📘 Custom OpenAPI Schema
# ---------------------------
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

# ---------------------------
# 📦 Include Routers
# ---------------------------
app.include_router(deploy_router)
app.include_router(logs_router)
app.include_router(health_router)
app.include_router(auth_router)

app.state.limiter = limiter

# ✅ Rate Limit Exception Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Terlalu banyak percobaan. Coba lagi nanti."}
    )

app.add_middleware(SlowAPIMiddleware)

# ---------------------------
# 🌐 CORS Setup
# ---------------------------
origins = [
    "http://localhost:8082",
    "https://dev-trigger.mugshot.dev/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 🔐 Load Env Configs (optional)
# ---------------------------
SECRET_KEY = config("SECRET_KEY")