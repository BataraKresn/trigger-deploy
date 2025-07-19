from fastapi import APIRouter, HTTPException
import os
import logging

router = APIRouter()

@router.get("/api/logs")
async def get_logs():
    try:
        logs_dir = "./trigger-logs/"
        logs = []

        for log_file in os.listdir(logs_dir):
            with open(os.path.join(logs_dir, log_file), 'r') as file:
                logs.append({"file": log_file, "content": file.read()})

        return {"status": "success", "message": "Logs retrieved", "data": logs}

    except Exception as e:
        logging.error(f"Error retrieving logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/api/logs/{filename}")
async def get_log_content(filename: str):
    try:
        logs_dir = "./trigger-logs/"
        file_path = os.path.join(logs_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Log file not found")

        with open(file_path, 'r') as file:
            content = file.read()

        return {"status": "success", "message": "Log content retrieved", "data": content}

    except Exception as e:
        logging.error(f"Error retrieving log content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
