from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import logging

router = APIRouter()

class DeployRequest(BaseModel):
    ip: str
    user: str
    path: str

@router.post("/api/deploy")
async def deploy_server(payload: DeployRequest):
    try:
        # Validate input
        if not payload.ip or not payload.user or not payload.path:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Execute deploy-wrapper.sh
        command = f"./deploy-wrapper.sh {payload.ip} {payload.user} {payload.path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Deploy failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Deploy failed: {result.stderr}")

        logging.info(f"Deploy succeeded: {result.stdout}")
        return {"status": "success", "message": "Deploy succeeded", "data": result.stdout}

    except Exception as e:
        logging.error(f"Error during deploy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
