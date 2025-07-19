from fastapi import APIRouter

router = APIRouter()

@router.get("/api/deploy-servers")
def deploy_servers():
    return {"message": "Deploy servers endpoint"}
