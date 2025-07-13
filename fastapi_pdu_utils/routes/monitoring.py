from fastapi import APIRouter, HTTPException
import requests as rq
from utils.models import InputDataModel
from utils.enums import  LogFile
from utils.queues import (
    queue_maintenance,
    queue_temperature,
    queue_migration,
    queue_gain_before,
    queue_gain_after
)

router = APIRouter(prefix="/prom", tags=["Monitoring"])

@router.post("/start_monitoring")
async def start_monitoring_scripts(inputs: InputDataModel):
    """Start scripts by sending a request to the remote Flask server"""
    print(inputs.dict())
    queue_maintenance.empty_queue()
    queue_temperature.empty_queue()
    queue_migration.empty_queue()
    queue_gain_before.empty_queue()
    queue_gain_after.empty_queue()
    response = rq.post("http://10.150.1.200:5000/start", json=inputs.dict()).json()
    return response


@router.post("/stop_monitoring")
async def stop_monitoring_scripts():
    """Stop scripts by sending a request to the remote Flask server"""
    response = rq.post("http://10.150.1.200:5000/stop").json()
    return response


@router.get("/monitoring_status")
async def check_monitoring_status():
    """Check script status on remote server"""
    response = rq.get("http://10.150.1.200:5000/status").json()
    return response


@router.get("/monitoring_logs")
async def check_monitoring_logs(script_name: LogFile = LogFile.default):
    """Check script logs on the Flask server by calling Flask API."""
    try:
        if script_name == LogFile.default:
            response = rq.get("http://10.150.1.200:5000/logs")
        else:
            response = rq.get("http://10.150.1.200:5000/logs", params={"script_name": script_name.value})

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("error", "Error fetching logs"))
    except rq.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling Flask API: {str(e)}")


@router.get("/monitoring")
async def get_monitoring_conf():
    mon_conf = rq.get("http://10.150.1.30:5001/get-moni-conf").json()
    return {
        "data_center": "BLC",
        "id": 1,
        "status": "open",
        "optimization_space": mon_conf.get("optimization_space", {})
    }
