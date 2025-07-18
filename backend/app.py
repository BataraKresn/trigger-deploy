from fastapi import FastAPI
from routes.deploy import router as deploy_router
from routes.logs import router as logs_router
from routes.health import router as health_router
from routes.auth import router as auth_router
from loguru import logger
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Configure loguru
logger.add("logs/backend_{time}.log", rotation="1 day", retention="7 days", level="INFO")

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

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

app.include_router(deploy_router)
app.include_router(logs_router)
app.include_router(health_router)
app.include_router(auth_router)
