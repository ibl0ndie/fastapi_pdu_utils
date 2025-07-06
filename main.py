from fastapi import FastAPI, Depends, Request ,HTTPException, Body
import re
from handler_funcs import *
# from decimal import Decimal
from database import *
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import json
import os
import subprocess
# from fastapi.responses import JSONResponse
# import paramiko
import psutil
from fabric import Connection, Group, SerialGroup
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from informative_scripts import *
import requests as rq
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, RootModel, parse_obj_as, ValidationError, Field, validator
from enum import Enum
import aiohttp
import asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from utils.queue import Queue
from utils.models import (
    ApprovalRequest, MigrationDecModel, TemperatureModel, 
    # ... import other models as needed
)
from utils.enums import LogFile
from routes import migration

app = FastAPI()
origins = ["*"]

message_ew = {'messages': [{'message': 'Current power utilization :420.5 Watt <br>Proposed power utilization: 405.3<br>Expected power gain: %3.58', 'show': 1, 'message_id': 1}]}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    FastAPICache.init(
        InMemoryBackend()
    )

# Main endpoint
@app.on_event("startup")
async def startup():
    import aiohttp
    app.state.session = aiohttp.ClientSession()

    set_global_app(app)  # make app available to metrics.py

@app.on_event("shutdown")
async def shutdown():
    await app.state.session.close()




queue_maintenance = Queue("maintenance_save.json")
queue_temperature = Queue("temperature_save.json")
queue_migration = Queue("migration_save.json")
#queue_migration_prime = Queue("migration_prime_save.json")
queue_migration.change_max_amount(1)
#queue_migration_prime.change_max_amount(1)
queue_gain_before = Queue("gain_before_save.json")
queue_gain_before.change_max_amount(1)
queue_gain_after = Queue("gain_after_save.json")
queue_gain_after.change_max_amount(1)
queue_placement = Queue("gain_vm_placement.json")
queue_placement.change_max_amount(1)

# queue = Queue()
# mainintenance_queue = Queue()
# migration_queue = Queue()

async def make_async_request(
    url: str,
    method: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generic aiohttp request handler with error handling.
    
    Args:
        url: Target URL
        method: HTTP method (GET/POST/PUT/DELETE)
        payload: Request body data
        headers: Custom headers
        timeout: Timeout in seconds
        
    Returns:
        JSON response as dict
        
    Raises:
        HTTPException: On request failure
    """
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method=method,
                url=url,
                json=payload,
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=502,
                        detail=f"Remote API error ({response.status}): {error_text}"
                    )
                
                return await response.json()
                
    except ValueError as e:
        raise HTTPException(400, detail=f"Invalid request data: {str(e)}")
    except aiohttp.ClientError as e:
        raise HTTPException(503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(500, detail=f"Unexpected error: {str(e)}")

app.include_router(migration_routes.router)

SSH_USER = "ubuntu"
SSH_KEY_PATH = "/home/ubuntu/myenv/myenv/ayposKeypair.pem"
STRESS_LEVELS = {
    "low": "stress -c 4 -t 30m",
    "medium": "stress -c 8 -t 30m",
    "high": "stress -c 12 -t 30m"
}



from routes.stress import router as stress_router

app.include_router(stress_router)


from routes.snmp import router as snmp_router

app.include_router(snmp_router)




import aiohttp
import asyncio


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

@app.get('/prom/pm_mac_details')
@cache(expire=20)  # Cache the result for 20 seconds
async def get_physical_mac_details():
    try:
        res = await fetch_data("http://10.150.1.30:5001/get-pm-conf")

        for i in res:
            res[i]['idle consumption'] = 114
            res[i]["memory_mb"] = float(res[i]["memory_mb"]) / 1024

        return {"res": res}

    except Exception as e:
        print(e)
        return {"error": str(e)}

@app.get('/prom/vm_mac_details')
@cache(expire=20)  # Cache the result for 20 seconds
async def get_mac_details():
    try:
        res = await fetch_data("http://10.150.1.30:5001/get-vm-conf")

        res = res['result']
        for i in res:
            res[i]['ram'] = float(res[i]['ram']) / 1024

        return {"res": res}

    except Exception as e:
        print(e)
        return {"error": str(e)}







#@app.get('/prom/pm_mac_details')
#async def get_physical_mac_details():
#
#    try:
#        res = rq.get("http://10.150.1.30:5001/get-pm-conf").json()
#
#        for i in res:
#            res[i]['idle consumption'] = 114
#            res[i]["memory_mb"] = float(res[i]["memory_mb"]) / 1024
            # res[i]['memory_mb'] = float(res[i]['memory_mb']
            
#        return {"res": res}

#    except Exception as e:
#        print(e)

#@app.get('/prom/vm_mac_details')
#async def get_mac_details():
#    res = rq.get("http://10.150.1.30:5001/get-vm-conf").json()
        
#    res = res['result']
#    for i in res:
#        res[i]['ram'] = float(res[i]['ram']) / 1024

#    return {"res": res}

from routes.monitoring import router as monitoring_router

app.include_router(monitoring_router)

"""
@app.get("/prom/phy_mac/{iplast}")
async def get_psutil_script_data_phy_machine(iplast):
    try:
        # Establish an SSH connection to the remote node
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        node_ip = "10.150.1." + iplast

        ssh.connect(node_ip, username="ubuntu", password="blc2022*")
        # Define the script to run on the remote node
        script = '''
import psutil

memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')

cpu_count = psutil.cpu_count()

total_memory = memory.total
available_memory = memory.available
used_memory = memory.used
free_memory = memory.free

disk_total = disk.total
disk_used = disk.used
disk_free = disk.free

print(f"{{'total_memory': {{total_memory}}, 'available_memory': {{available_memory}}, 'used_memory': {{used_memory}}, 'free_memory': {{free_memory}}, 'disk_total': {{disk_total}}, 'disk_used': {{disk_used}}, 'disk_free': {{disk_free}}}}}")
        '''

        # Execute the script on the remote node
        stdin, stdout, stderr = ssh.exec_command(script_vm_mac_details)
        data = stdout.read().decode('utf-8')
        ssh.close()

        return JSONResponse(content=data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

        """


# return success in post models
from routes.chart_data import router as chart_data_router
from routes.push_data import router as push_data_router


# Register routers
app.include_router(chart_data_router)
app.include_router(push_data_router)



#@app.post('/prom/push/migration_data_prime')
#async def push_chart_data_migration_prime(data: MigrationPrimeModel):
#    queue_migration_prime.push(data)
#    print(data)
#
#    return data




app.include_router(chart_data_router)



@app.get('/prom/migration/message')
async def get_migration_messages():
    return message_ew
    # return {'messages': [{'message': 'Virtual machine s88 can be migrated to compute3 from compute2. It will possibly save 14.6 watts meaning %2.7 energy saving.', 'show': 1, 'message_id': 1}, {'message': 'Virtual machine Redmine can be migrated to compute2 from compute3. It will possibly save 4.0 watts meaning %0.7 energy saving.', 'show': 1, 'message_id': 2}]}


#@app.get("/prom/get_chart_data/migrationprime")
#async def get_migration_primer():
#    
#    data = queue_migration_prime.get_data()
#    return {"data": data}


@app.get("/prom/phy_mac/{iplast}")
async def get_psutil_script_data_phy_machine(iplast):
    try:
        node_ip = "10.150.1." + iplast
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            #c.run("pip install psutil", hide=True)
            result = c.run("python3 -c '{}'".format(script_phy_mac), hide=True)
            # c.run("pip install psutil", hide=True)
            return {"res":result.stdout}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
            

# @app.get('/prom/random_migrate')
# def random_migrator(migrate_model: RandomMigrate):
#     ...


