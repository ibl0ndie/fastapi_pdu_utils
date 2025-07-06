from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import asyncio

from your_project.database import get_db
from your_project.models import SnmpMin, Snmp_30sec, Snmp_cur, Snmp_10
from your_project.snmp_utils import (
    get_actual_snmps_nmin, get_snmps_nmin, return_mixed_part, 
    get_ips2, handle_aver_last_min2, get_ips, return_cur,
    scraper_dict_cr, get_name_snmp, handle_aver_last_min, organize_data
)

router = APIRouter(prefix="/prom", tags=["SNMP Monitoring"])

@router.get('/snmp/n_min_aver_power/{i}')
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
        pup_p[key]['pf'] = 0.92324562
        pup_p[key]['energy'] /= 10

    pup_p['compute4']['energy'] /= 3 
    return pup_p

@router.get("/snmp/min")
async def get_snmp_min_aveage(db: Session = Depends(get_db)):
    data = db.query(SnmpMin).all()
    titles = ["time_stamp", "voltage", "current", "pf", "energy", "power"]
    values = str(data[0].snmpdata).split(',')
    return {titles[i]: values[i] for i in range(len(titles))}

@router.get('/snmpcsv/hour/{computename}')
async def get_snmp_csv_data_hour(computename: str):
    compute, n = computename.split('&')
    get_snmps_nmin(int(n), 'h', compute)
    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')

@router.get('/snmpcsv/day/{computename}')
async def get_snmp_csv_data_day(computename: str):
    compute, n = computename.split('&')
    get_snmps_nmin(int(n), 'd', compute)
    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')

@router.get('/snmpcsv/minute/{computename}')
async def get_snmp_csv_data_minute(computename: str):
    compute, n = computename.split('&')
    get_snmps_nmin(int(n), compute_name=compute)
    return FileResponse(f'/home/ubuntu/myenv/myenv/{compute}.csv')

@router.get("/mixed/aver30")
async def get_30_sec_average_data_mixed(db: Session = Depends(get_db)):
    posts = db.query(Snmp_30sec).all()
    titles = ["voltage", "current", "pf", "energy", "power"]
    totals = [0] * len(titles)

    for post in posts:
        values = post.snmpdata.split(',')[1:]
        for i in range(len(totals)):
            totals[i] += float(values[i])

    avg = {titles[i]: round(totals[i] / len(posts), 4) for i in range(len(totals))}
    return {**return_mixed_part(), **avg}

@router.get("/aver/lastmin/{minu}")
@cache(expire=20)
async def get_last_n_min_average_data(minu: int):
    ip_dict = await get_ips2()
    tasks = [handle_aver_last_min2(ip_dict[server], False, int(minu)) for server in ip_dict]
    results = await asyncio.gather(*tasks)
    return {server: results[i] for i, server in enumerate(ip_dict)}

@router.get("/cur")
async def get_current_prometheus_data():
    ip_dict = get_ips()
    return {server: return_cur(ip_dict[server]) for server in ip_dict}

@router.get("/snmps/cur")
async def get_computes_snmp_cur_data():
    return scraper_dict_cr()

@router.get("/snmp/cur")
async def get_snmp_cur_data(db: Session = Depends(get_db)):
    compute3_power = get_name_snmp()['compute3']
    post = db.query(Snmp_cur).first()
    titles = ["voltage", "current", "pf", "energy", "power"]
    values = post.snmpdata.split(',')[1:]
    data = {titles[i]: round(float(values[i]), 4) for i in range(len(values))}
    data['power'] = str(compute3_power)
    return data

@router.get("/snmp")
async def get_snmp_10_min_data(db: Session = Depends(get_db)):
    posts = db.query(Snmp_10).all()
    titles = ["voltage", "current", "pf", "energy", "power"]
    totals = [0] * len(titles)

    for post in posts:
        values = post.snmpdata.split(',')[1:]
        for i in range(len(totals)):
            totals[i] += float(values[i])

    avg = {titles[i]: round(totals[i] / len(posts), 4) for i in range(len(totals))}
    return avg

@router.get("/smoothaver/{nhour}")
async def get_smooth_n_hour_data(nhour: int):
    return handle_aver_last_min(0, last10=None, go_hour_back=nhour)

@router.get("/day/{nday}")
async def get_last_n_day_csv_data_and_download(nday: int):
    organize_data(nday)
    return FileResponse("/home/ubuntu/out/thefactory/1.csv")
