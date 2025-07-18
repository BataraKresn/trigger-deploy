from fastapi import APIRouter

router = APIRouter()

@router.get("/deploy-servers")
def deploy_servers():
    return {"message": "Deploy servers endpoint"}
