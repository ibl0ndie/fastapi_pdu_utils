from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from fabric import Connection, Group
from pydantic import BaseModel, Field, validator
import asyncio
import time

from settings import SSH_USER, SSH_KEY_PATH, STRESS_LEVELS  # Adjust this import to your actual path

router = APIRouter(prefix="/stress", tags=["Stress"])

# ------------------- MODELS -------------------

class VMsRequest(BaseModel):
    vms: List[str]

class StressRequest(BaseModel):
    vms: List[str] = Field(..., min_items=1, example=["10.150.1.146"])
    level: str = "medium"
    force: bool = False

    @validator('level')
    def validate_level(cls, v):
        if v not in STRESS_LEVELS:
            raise ValueError("Invalid level. Use low/medium/high")
        return v

# ------------------- HELPERS -------------------

def get_connections(ips: List[str]) -> Group:
    if not ips:
        raise ValueError("At least one VM must be specified")
    connection_strings = [f"{SSH_USER}@{ip}" for ip in ips]
    return Group(*connection_strings, connect_kwargs={"key_filename": SSH_KEY_PATH})

def is_stress_running(connection: Connection) -> Optional[List[str]]:
    try:
        result = connection.run("pgrep -a stress", hide=True, warn=True, in_stream=False)
        if result.ok and result.stdout.strip():
            return result.stdout.strip().split('\n')
        return None
    except Exception as e:
        raise RuntimeError(f"Failed to check stress on {connection.host}: {str(e)}")

def verify_stress_stopped(connection: Connection):
    for _ in range(3):
        pids = is_stress_running(connection)
        if not pids:
            return True
        connection.run("pkill -9 -f stress", hide=True, in_stream=False)
        time.sleep(0.5)
    return False

async def run_in_threadpool(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)

# ------------------- ROUTES -------------------

@router.post("/status")
async def check_stress_status(vms: List[str] = Body(..., min_items=1)):
    try:
        group = await run_in_threadpool(get_connections, vms)
        results = {}

        def check_single(connection):
            try:
                pids = is_stress_running(connection)
                return {
                    "is_running": pids is not None,
                    "processes": pids
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "is_running": False,
                    "processes": None
                }

        futures = [run_in_threadpool(check_single, conn) for conn in group]
        results_list = await asyncio.gather(*futures)
        for conn, result in zip(group, results_list):
            results[conn.host] = result

        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start")
async def start_stress(request: StressRequest):
    group = get_connections(request.vms)
    command = f"nohup {STRESS_LEVELS[request.level]} >/dev/null 2>&1 &"
    results = {}

    for connection in group:
        pids = is_stress_running(connection)
        if not request.force and pids:
            results[connection.host] = {
                "status": "skipped",
                "reason": "Stress already running",
                "processes": pids
            }
        else:
            if request.force:
                connection.run("pkill -9 -f stress", hide=True, warn=True, in_stream=False)
            connection.run(command, hide=True, in_stream=False)
            new_pids = is_stress_running(connection)
            results[connection.host] = {
                "status": "started",
                "command": command,
                "pid": new_pids
            }
    return {"results": results}


@router.post("/stop")
async def stop_stress(vms: List[str] = Body(..., min_items=1)):
    try:
        group = get_connections(vms)
        results = {}

        async def process_host(connection):
            try:
                pids = await run_in_threadpool(is_stress_running, connection)
                if not pids:
                    results[connection.host] = {"status": "already_stopped"}
                    return

                await run_in_threadpool(lambda: connection.run("pkill -9 -f stress", hide=True, warn=True, in_stream=False))
                stopped = await run_in_threadpool(verify_stress_stopped, connection)
                results[connection.host] = {
                    "status": "stopped" if stopped else "partial",
                    "killed": len(pids),
                    "previous_pids": pids
                }
            except Exception as e:
                results[connection.host] = {
                    "status": "failed",
                    "error": str(e)
                }

        await asyncio.gather(*[process_host(conn) for conn in group])
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

