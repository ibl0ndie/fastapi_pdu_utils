from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import aiohttp
import asyncio
import httpx

# Assume these are defined/imported
from some_module import queue_migration, queue_gain_before, queue_temperature, make_async_request, get_ips, handle_aver_last_min, get_snmps
from fabric import Connection

router = APIRouter()


@router.post("/prom/migration/decisions")
async def start_migration(request: Request, run_migration: bool = False):
    if not run_migration:
        return {"message": "Migration declined"}

    try:
        timeout = aiohttp.ClientTimeout(total=None)
        connector = aiohttp.TCPConnector(force_close=False, limit=None)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers={"Accept": "text/event-stream"}) as session:
            async with session.post("http://10.150.1.200:5000/run-migration", raise_for_status=False) as response:
                if response.status != 200:
                    error = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Flask API error: {error}")

                async def event_stream():
                    try:
                        async for chunk in response.content.iter_chunks():
                            if await request.is_disconnected():
                                print("Client disconnected")
                                break
                            yield chunk[0]
                    except asyncio.CancelledError:
                        print("Stream cancelled")
                        raise
                    except Exception as e:
                        print(f"Stream error: {str(e)}")
                        raise

                return StreamingResponse(event_stream(), media_type=response.headers.get('Content-Type', 'text/event-stream'))
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Connection to Flask API failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/prom/migration/decisions2")
async def start_migration2(run_migration: bool):
    if not run_migration:
        queue_migration.queue.pop(0)
        queue_migration.length = len(queue_migration.queue)
        return {"message": "Migration declined"}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None)) as session:
            async with session.post("http://10.150.1.200:5000/run-migration") as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Flask API returned error: {error_detail}")

                async def generate():
                    async for chunk in response.content.iter_any():
                        print(chunk.decode('utf-8').strip())
                        yield chunk

                return StreamingResponse(generate(), media_type=response.headers.get('content-type', 'text/plain'),
                                         headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prom/aver")
async def get_last_10_min_average_data():
    ip_dict = get_ips()
    data_holder = {server: handle_aver_last_min(ip_dict[server]) for server in ip_dict}
    return data_holder


@router.get('/prom/snmp/cur_power')
async def get_current_powers_computes():
    return get_snmps()


@router.get('/prom/stress/high')
async def start_high_stress():
    try:
        node_ip = "10.150.1.35"
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            c.run("nohup stress -c 12 -t 10m >/dev/null 2>&1 &", hide=True)
            return {"status": "success"}
    except Exception as e:
        print(e)


@router.get('/prom/stress/mid')
async def start_mid_stress():
    try:
        node_ip = "10.150.1.35"
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            c.run("nohup stress -c 8 -t 10m >/dev/null 2>&1 &", hide=True)

        with Connection(host="10.150.1.34", user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            c.run("nohup stress -c 8 -t 10m >/dev/null 2>&1 &", hide=True)

        return {"status": "success"}
    except Exception as e:
        print(e)


@router.get('/prom/stress/low')
async def start_low_stress():
    try:
        node_ip = "10.150.1.35"
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            c.run("nohup stress -c 4 -t 10m >/dev/null 2>&1 &", hide=True)
            return {"status": "success"}
    except Exception as e:
        print(e)
