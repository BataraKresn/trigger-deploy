from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import logging

router = APIRouter()

class HealthResponse(BaseModel):
    ip: str
    pingTime: str
    dnsResolved: str
    memoryUsage: int
    ramUsage: int
    diskUsage: int
    status: str

@router.get("/api/health")
def health_check():
    return {"status": "Healthy"}

@router.get("/api/health/{ip}")
async def get_health(ip: str):
    try:
        # Simulate health check (ping, DNS, RAM, etc.)
        ping_result = subprocess.run(["ping", "-c", "1", ip], capture_output=True, text=True)
        dns_resolved = f"server.{ip}"  # Example DNS resolution
        memory_usage = 65  # Example memory usage
        ram_usage = 70  # Example RAM usage
        disk_usage = 50  # Example disk usage

        status = "up" if ping_result.returncode == 0 else "down"

        data = HealthResponse(
            ip=ip,
            pingTime="20 ms",  # Example ping time
            dnsResolved=dns_resolved,
            memoryUsage=memory_usage,
            ramUsage=ram_usage,
            diskUsage=disk_usage,
            status=status
        )

        return {"status": "success", "message": "Health check completed", "data": data.dict()}

    except Exception as e:
        logging.error(f"Error during health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
