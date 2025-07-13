from fastapi import APIRouter 
from fastapi_cache.decorator import cache

import asyncio

from handler_funcs import (
    get_actual_snmps_nmin,
    get_ips2,
    handle_aver_last_min2,
)

router = APIRouter(prefix="/prom", tags=["SNMP Monitoring"])

#THIS IS SNMP DATA
@router.get("/snmp/n_min_aver_power/{i}")
async def get_last_n_min_powers_computes(i: int):
    data = get_actual_snmps_nmin(i)
    modified_data = {
        key: {
            new_key.replace("pdu_", ""): value for new_key, value in data[key].items()
        }
        for key in data.keys()
    }
    pup_p = {key: modified_data[key] for key in modified_data}
    for key in pup_p:
        pup_p[key]["pf"] = 0.92324562
        pup_p[key]["energy"] /= 10

    pup_p["compute4"]["energy"] /= 3
    return pup_p


# THIS IS NODE EXPORTER DATA
@router.get("/aver/lastmin/{minu}")
@cache(expire=20)
async def get_last_n_min_average_data(minu: int):
    ip_dict = await get_ips2()
    tasks = [
        handle_aver_last_min2(ip_dict[server], False, int(minu)) for server in ip_dict
    ]
    results = await asyncio.gather(*tasks)
    return {server: results[i] for i, server in enumerate(ip_dict)}
