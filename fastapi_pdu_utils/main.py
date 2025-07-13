from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from typing import Any, Dict, Optional
import aiohttp

# Local imports
from final.utils.async_request import fetch_data
from handler_funcs import *
from informative_scripts import *
from routes.monitoring import router as monitoring_router
from routes.chart_data import router as chart_data_router
from routes.push_data import router as push_data_router
from routes.migration import router as migration_router
from routes.stress import router as stress_router
from routes.snmp import router as snmp_router
from utils.enums import LogFile
from utils.models import ApprovalRequest, MigrationDecModel, TemperatureModel
from utils.queue import Queue

app = FastAPI()
origins = ["*"]

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration
app.include_router(monitoring_router)
app.include_router(chart_data_router)
app.include_router(push_data_router)
app.include_router(migration_router)
app.include_router(stress_router)
app.include_router(snmp_router)

@app.on_event("startup")
async def startup_event():
    FastAPICache.init(InMemoryBackend())
    app.state.session = aiohttp.ClientSession()
    set_global_app(app)  # Make app available to metrics.py

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.session.close()

@app.get("/prom/pm_mac_details")
@cache(expire=20)
async def get_physical_mac_details():
    try:
        res = await fetch_data("http://10.150.1.30:5001/get-pm-conf")
        
        for i in res:
            res[i]["idle consumption"] = 114
            res[i]["memory_mb"] = float(res[i]["memory_mb"]) / 1024
        
        return {"res": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prom/vm_mac_details")
@cache(expire=20)
async def get_mac_details():
    try:
        res = await fetch_data("http://10.150.1.30:5001/get-vm-conf")
        res = res["result"]
        
        for i in res:
            res[i]["ram"] = float(res[i]["ram"]) / 1024
        
        return {"res": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))