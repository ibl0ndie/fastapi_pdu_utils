from fastapi import FastAPI, Depends
import re
from handler_funcs import *
# from decimal import Decimal
from database import *
from fastapi.responses import FileResponse, JSONResponse
import os
import subprocess
# from fastapi.responses import JSONResponse
# import paramiko
import psutil
from fabric import Connection
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/prom/aver/{machine}")
async def get_last_10_min_average_data(machine: int):

    serv = handle_auto_ip(machine)
    print(serv)
    return handle_aver_last_min(serv)


@app.get("/prom/mixed/aver30")
async def get_30_sec_average_data_mixed(db: Session = Depends(get_db)):

    posts = db.query(Snmp_30sec).all()
    initi = [0,0,0,0, 0]
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    for post in posts:
        adata = post.snmpdata
        # print(post.snmpdata)
        l = adata.split(',')
        td = l[0]
        l = l[1:len(l)]
        
        # t = post.timedata

        for index in range(len(l)):
            initi[index] += float(l[index])
            # c=index

    for i in range(len(initi)):

        emp[titles[i]] = round(initi[i]/len(posts), 4)

    print(len(initi), len(l))
    print(len(post.snmpdata))
    # print(initi)
    # return emp # {"data": initi}
    # posts = db.query
    # return return_mixed_part()
    dc = {**return_mixed_part(), **emp}
    # dc["ts"] = td
    return dc # {**return_mixed_part(), **emp}["ts"] = td
    # didnt work out neither
    # return(emp.update(return_mixed_part()))
    
    # return return_mixed_part() | emp
    # naah for Python 3.9, too lazy to upgrade


@app.get("/prom/aver/lastmin/{minu}")
async def get_last_n_min_average_data(minu: int):
    return handle_aver_last_min(0, False, int(minu))


@app.get("/prom/cur/{machine}")
async def get_current_prometheus_data(machine: int):
    serv = handle_auto_ip(machine)
    return return_cur(serv)


@app.get("/prom/snmp/cur")
async def get_snmp_cur_data(db: Session = Depends(get_db)):

    post = db.query(Snmp_cur).first()
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    l = post.snmpdata.split(',')
    l = l[1:len(l)]

    for i in range(len(l)):

        emp[titles[i]] = round(float(l[i]), 4)

    return emp


@app.get("/prom/snmp")
async def get_snmp_10_min_data(db: Session = Depends(get_db)):
     
    posts = db.query(Snmp_10).all()
    initi = [0,0,0,0, 0]
    emp = {}
    titles = ["voltage", "current", "pf", "energy", "power"]

    for post in posts:
        adata = post.snmpdata
        # print(post.snmpdata)
        l = adata.split(',')
        l = l[1:len(l)]
        t = post.timedata
        
        for index in range(len(l)):
            initi[index] += float(l[index])
            # c=index
   
    for i in range(len(initi)):

        emp[titles[i]] = round(initi[i]/len(posts), 4)

    # print(initi)
    return emp # {"data": initi}
    # posts = db.query

"""
@app.get("/prom/last/{stri}")
def get_last_n_time_average_data(stri: str):

    match = re.search(r'day=(\d+);hour=(\d+);minute=(\d+)', stri)

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
    else:
        print("Pattern not found in the endpoint string.")


@app.get("/prom/interval/{stri}")
def get_an_interval_average_data(stri: str):
    
    start_match = re.search(r'start=(\d{2}):(\d{2})_(\d{2})_(\d{2})_(\d{4})', input_string)
    end_match = re.search(r'end=(\d{2}):(\d{2})_(\d{2})_(\d{2})_(\d{4})', input_string)
    if start_match and end_match:
        start_hour = int(start_match.group(1))
        start_minute = int(start_match.group(2))
        start_day = int(start_match.group(3))
        start_month = int(start_match.group(4))
        start_year = int(start_match.group(5))

        end_hour = int(end_match.group(1))
        end_minute = int(end_match.group(2))
        end_day = int(end_match.group(3))
        end_month = int(end_match.group(4))
        end_year = int(end_match.group(5))

    ...
"""

@app.get("/prom/smoothaver/{nhour}")
async def get_smooth_n_hour_data(nhour: int):
    return handle_aver_last_min(0, last10=None, go_hour_back=nhour)


@app.get("/prom/day/{nday}")
async def get_last_n_day_csv_data_and_download(nday:int):
    cmd = ["ls ../out"]
    organize_data(nday)

    # pass
    return FileResponse("/home/ubuntu/out/thefactory/1.csv")


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
        stdin, stdout, stderr = ssh.exec_command(script)
        data = stdout.read().decode('utf-8')
        ssh.close()

        return JSONResponse(content=data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

        """


@app.get("/prom/phy_mac/{iplast}")
async def get_psutil_script_data_phy_machine(iplast):
    try:
        node_ip = "10.150.1." + iplast
        with Connection(host=node_ip, user="ubuntu", connect_kwargs={"password": "blc2022*"}) as c:
            script = """
import psutil

memory = psutil.virtual_memory()
disk = psutil.disk_usage("/")

cpu_count = psutil.cpu_count()

total_memory = memory.total / (1024 ** 3)
available_memory= memory.available / (1024 ** 3)
used_memory= memory.used / (1024 ** 3)
free_memory= memory.free / (1024 ** 3)

disk_total = disk.total / (1024 ** 3)
disk_used= disk.used / (1024 ** 3)
disk_free= disk.free / (1024 ** 3)

values = [f"{cpu_count:.2f}", f"{total_memory:.3f}", f"{available_memory:.3f}", f"{used_memory:.3f}", f"{free_memory:.3f}", f"{disk_total:.3f}", f"{disk_used:.3f}", f"{disk_free:.3f}"]
names = ["cpu_count","total_memory(GB)","available_memory(GB)","used_memory(GB)","free_memory(GB)","disk_total(GB)","disk_used(GB)","disk_free(GB)"]

def make_queue(value, name):
    message_queue = ""
    for i in range (len(value)):
        if i < len(value)-1:
            message_queue += f"{name[i]}-{value[i]}/"
        else:
            message_queue += f"{name[i]}-{value[i]}"
    return message_queue

message= make_queue(values,names)
print(message)
"""
            c.run("pip install psutil", hide=True)
            result = c.run("python3 -c '{}'".format(script), hide=True)
            # c.run("pip install psutil", hide=True)
            return {"res":result.stdout}
    except Exception as e:
        return {error: f"An error occurred: {e}"}
            

