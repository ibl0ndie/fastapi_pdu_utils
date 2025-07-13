import json
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal

import aiohttp
import numpy as np
import pandas as pd
import requests as rq

from env import *
from organizer import *
from settings import *

_fastapi_app = None

def set_global_app(app):
    global _fastapi_app
    _fastapi_app = app
    print("Global app set")

# ------------------- ASYNC FUNCTIONS (USED) -------------------
async def get_ips2():
    session = _fastapi_app.state.session

    data_js = await fetch_json2(session, f"{prometheus_domain}/api/v1/query?query=node_load1")
    node_json = await fetch_json2(session, f"{prometheus_domain}/api/v1/query?query=node_uname_info")

    serv_dict = {}
    ct = 0
    for nodename in node_json['data']['result']:
        nodename = nodename['metric']["instance"].split(':')[0]
        serv_dict[nodename] = ct
        ct += 1

    print(f"IPs retrieved: {serv_dict}")
    return serv_dict

async def handle_aver_last_min2(server, last10=True, nmin=10):
    now = datetime.utcnow()
    start = now - timedelta(minutes=nmin)

    start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    print(f"Handling average for last {nmin} minutes, server: {server}")
    return await handleit2(start, end, step, step_func, server)

async def handleit2(start, end, step, step_func, server):
    df_nodes = pd.read_csv("csv/nodes2.csv")
    session = _fastapi_app.state.session
    json_h = {}

    for _, col in df_nodes.iterrows():
        query_name = col["query_name"]
        query = col["query"]
        instance = f'{await return_instance2("node", st_num=server)}'
        url = curly_organizer2(query, instance, step_func)
        url = organize_url2(url, start, end, step)
        metric_data_node = await fetch_json2(session, url)
        try:
            if len(metric_data_node['data']['result']) == 0:
                print(f"No data for query: {query_name}")
                continue
            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])[:, 1].astype(float)
            json_h[query_name] = float(np.mean(metric_data_node).round(4))
            print(f"Processed {query_name}: {json_h[query_name]}")
        except Exception as e:
            print(f"Error processing data: {e}")
            continue

    return json_h

async def fetch_json2(session, url):
    try:
        print(f"Fetching URL: {url}")
        async with session.get(url) as resp:
            json_data = await resp.json()
            if "data" not in json_data:
                print(f"⚠️ Invalid Prometheus response: {json_data}")
                return {}
            return json_data
    except Exception as e:
        print(f"❌ Error fetching from Prometheus: {e}")
        return {}

def curly_organizer2(string, ip, step_func="5m"):
    return string.replace("$", ip).replace("#", step_func)

def organize_url2(query, start, end, step="5s"):
    url_str = query.replace("\"", "%22").replace("+", "%2B").replace("*", "%2A")
    return f"{prometheus_domain}/api/v1/query_range?query={url_str}&start={start}&end={end}&step={step}"

async def return_instance2(which="", start=give_default_dates()[0], end=give_default_dates()[1], st_num=0):
    print(f"Returning instance for {which} at index {st_num}")
    async with aiohttp.ClientSession() as session:
        if which == "node":
            query = "node_load1"
            url = f"http://localhost:9090/api/v1/query?query={query}&start={start}&end={end}&step=30s"
            data = await fetch_json2(session, url)
            result = data['data']['result'][st_num]['metric']['instance']
            return f'"{result}"'

        elif which == "libvirt":
            query = "libvirt_domain_info_vstate"
            url = f"http://localhost:9090/api/v1/query_range?query={query}&start={start}&end={end}&step=30s"
            async with session.get(url) as response:
                data = await response.json()
            result = data['data']['result'][st_num]['metric']['instance']
            return f'"{result}"'

        print("Invalid instance type requested")
        return -1

# ------------------- SYNCHRONOUS FUNCTIONS -------------------
def get_actual_snmps_nmin(nmin):
    print(f"Getting actual SNMPs for last {nmin} minutes")
    end_1 = datetime.utcnow()
    req = rq.get(f'{prometheus_domain}/api/v1/query?query=pdu_power').json()
    compute_order = {}
    data_len = len(req['data']['result'])

    for i in range(data_len):
        compute_order[req['data']['result'][i]['metric']['compute_id']] = i

    start_1 = end_1 - timedelta(minutes=nmin)
    emp = {}

    for i in compute_order:
        start = start_1.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end_1.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        pdu_list = ['pdu_power', 'pdu_energy', 'pdu_current', 'pdu_voltage', 'pdu_pf', 'time_stamp']
        data_d = {}

        for elem in pdu_list:
            if elem == 'time_stamp':
                query = f"{prometheus_domain}/api/v1/query_range?query=pdu_pf&start={start}&end={end}&step=1s"
                data = rq.get(query).json()
                time_data = [i[0] for i in data['data']['result'][compute_order[i]]['values']]
            else:
                query = f"{prometheus_domain}/api/v1/query_range?query={elem}&start={start}&end={end}&step=1s"
                data = rq.get(query).json()
                data_arr = [float(i[1]) for i in data['data']['result'][compute_order[i]]['values']]
                aver = sum(data_arr) / len(data_arr)
                data_d[elem] = aver
                print(f"Processed {elem} for {i}: {aver}")
        
        emp[i] = data_d

    return emp

def handle_aver_last_min(server, last10=True, nmin=10, go_hour_back=None):
    print(f"Handling average for server {server}, last10={last10}, nmin={nmin}, go_hour_back={go_hour_back}")
    now = datetime.now()
    start = now - timedelta(minutes=nmin)
    
    def handleit(start, end, step, step_func, server):
        df_nodes = pd.read_csv("csv/nodes2.csv")
        json_h = {}

        for name, col in df_nodes.iterrows():
            query_name = col["query_name"]
            query = col["query"]
            try:
                instance = f'{return_instance("node", st_num=server)}'
            except:
                print("error")
                exit(1)

            url = curly_organizer(query, instance, step_func)
            url = organize_url(url, start, end, step)
            metric_data_node = rq.get(url).json()
            print(f"Response for {query_name}: {metric_data_node}")

            try:
                if len(metric_data_node['data']['result']) == 0:
                    print(f"No data for {query_name}")
                    continue
            except:
                print("Potential time error. Please check if start and end times relevant.")
                continue
            
            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])
            metric_data_node = metric_data_node[:,1].reshape(-1)
            metric_data_node = metric_data_node.astype(float)
            meann = np.mean(metric_data_node).round(4)
            json_h[query_name] = float(meann)
            print(f"Processed {query_name}: {meann}")
        
        return json_h

    if last10:
        now = datetime.now()
        start = now - timedelta(minutes=10)
        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        now = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return handleit(start, now, step, step_func, server)
    else:
        if go_hour_back:
            holder = None
            for i in range(go_hour_back):
                end_time = now - timedelta(hours=i)
                start_time = now - timedelta(hours=i+1)
                end = end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                start = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                print(f"Processing hour {i}: {start} to {end}")
                result = handleit(start, end, step, step_func, server)
                if holder is None:
                    holder = pd.DataFrame(result, index=[0])
                else:
                    holder = pd.concat((holder, pd.DataFrame(result, index=[0])), axis=0)
            holder = holder.mean()
            return holder.to_dict()
        else:
            now = datetime.now()
            start = now - timedelta(minutes=nmin)
            start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            now = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            return handleit(start, now, step, step_func, server)

def get_all_pdu_metrics():
    print("Getting all PDU metrics")
    power_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_power").json()
    energy_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_energy").json()
    current_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_current").json()
    voltage_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_voltage").json()
    pf_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_pf").json()
    return power_data_js, energy_data_js, current_data_js, voltage_data_js, pf_data_js

def get_ips():
    print("Getting IPs")
    data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=node_load1").json()
    node_json = rq.get(f"{prometheus_domain}/api/v1/query?query=node_uname_info").json()
    serv_dict = {}
    ct = 0
    
    for nodename in node_json['data']['result']:
        nodename = nodename['metric']["instance"].split(':')[0]
        serv_dict[nodename] = ct
        ct += 1

    print(f"IP mapping: {serv_dict}")
    return serv_dict

def handle_auto_ip(serv_num):
    print(f"Handling auto IP for server number: {serv_num}")
    data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=node_load1").json()
    ct = 0

    for data in data_js['data']['result']:
        inst = data['metric']['instance']
        dotsp = inst.split('.')[-1].split(":")[0]
        if serv_num == int(dotsp):
            print("---------------------------------------------------")
            print(f"Found match at index {ct}")
            return ct
        ct += 1

def return_cur(server):
    print(f"Returning current metrics for server: {server}")
    ifserv = server or server == 0
    server = server if ifserv else 0
    df_nodes = pd.read_csv("csv/nodes2.csv")
    data = {}

    for name, col in df_nodes.iterrows():
        query_name = col["query_name"]
        query = col["query"]
        instance = f'{return_instance("node", st_num=server)}'
        url = curly_organizer(query, instance, step_func)
        url = f'{prometheus_domain}/api/v1/query?query={url}'
        metric_data_node = rq.get(url).json()
        print(f"Raw response for {query_name}: {metric_data_node}")

        try:
            if len(metric_data_node['data']['result']) == 0:
                print(f"No data for {query_name}")
                continue
        except:
            print("Potential time error. Please check if start and end times relevant.")
            continue

        metric_data_node = np.array(metric_data_node['data']['result'][0]['value'])
        metric_data_node = metric_data_node[1].reshape(-1)
        metric_data_node = metric_data_node.astype(float)
        data[query_name] = float(metric_data_node.round(4))
        print(f"Current value for {query_name}: {data[query_name]}")
    
    if not ifserv:
        for key in data:
            data[key] = 0
    return data

def organize_data(day):
    print(f"Organizing data for day: {day}")
    setting_file = open("/home/ubuntu/data_collector/prometheus-api-get-metric-data-main/src/settings.py", "w")
    setting_file.write(f"day = {day}\nhour = 0\nminute = 0\nsecond_in = 0\nstep = '2s'\nstep_func = '30s'\ndecimal_limit = 3\nlog = []")
    setting_file.close()

    subprocess.run(["python3", "/home/ubuntu/data_collector/prometheus-api-get-metric-data-main/src/main.py"])
    subprocess.run(["python3", "/home/ubuntu/out/edit.py"])
    subprocess.run(["python3", "/home/ubuntu/out/thefactory/remover.py"])

    proc = subprocess.Popen(["ls", "../../out"], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    exitcode = proc.returncode
    lslist = stdout.decode("utf-8").split('\n')[:-1]
    compute2 = []
    snmp = []

    for files in lslist:
        if files.startswith("compute3"):
            compute2.append(files)
        elif files.startswith("snmp"):
            snmp.append(files)

    print(f"Found compute files: {compute2}")
    print(f"Found snmp files: {snmp}")

    sns_times = []
    snmp_order_time = []
    snmp_end_time = []

    for sns in snmp:
        time = sns[16:30]
        holl = time.replace("_", " ").replace("T", " ").replace(":", " ").replace("-", " ")
        print(f"SNMP start time: {holl}")
        sns_times.append(holl)
        snmp_order_time.append(holl)
        
        time_end = sns[40:56]
        holl_end = time_end.replace("_", " ").replace("T", " ").replace(":", " ").replace("-", " ")
        print(f"SNMP end time: {holl_end}")
        snmp_end_time.append(holl_end)

    compute2_time = []
    compute2_end = []
    
    for elems in compute2:
        time = elems[20:34]
        holl = time.replace("_", " ").replace("T", " ")
        compute_time = holl.replace("i", " ")
        print(f"Compute start time: {compute_time}")
        compute2_time.append(compute_time)
        
        time_end = elems[47:61]
        holl_end = time_end.replace("_", " ").replace("T", " ")
        compute_end = holl_end.replace("i", " ")
        print(f"Compute end time: {compute_end}")
        compute2_end.append(compute_end)
    
    now = datetime.now()
    start = now - timedelta(days=day)

    if True:
        compute_start = compute2_time[-1] + " 2023"
        compute_start_datetime_obj = datetime.strptime(compute_start, "%m %d %H %M %S %Y")
        compute_end = compute2_end[-1] + " 2023"
        compute_end_datetime_obj = datetime.strptime(compute_end, "%m %d %H %M %S %Y")

        for j in range(len(snmp_order_time)):
            snmp_start = snmp_order_time[j] + " 2023"
            snmp_start_datetime_obj = datetime.strptime(snmp_start, "%m %d %H %M %S %Y")
            snmp_end = snmp_end_time[j] + " 2023"
            snmp_end_datetime_obj = datetime.strptime(snmp_end, "%m %d %H %M %S %Y")
            
            print(f"Comparing: SNMP start {snmp_start_datetime_obj} vs Compute {compute_start_datetime_obj}-{compute_end_datetime_obj}")
            print(f"          SNMP end   {snmp_end_datetime_obj} vs Compute {compute_start_datetime_obj}-{compute_end_datetime_obj}")
            
            if ((snmp_start_datetime_obj >= compute_start_datetime_obj and 
                 snmp_start_datetime_obj <= compute_end_datetime_obj) or
                (snmp_end_datetime_obj >= compute_start_datetime_obj and 
                 snmp_end_datetime_obj <= compute_end_datetime_obj)):
                
                print(f"Matched SNMP file: {snmp[j]}")
                print(f"Matched compute file: {compute2[-1]}")
                subprocess.run(["cp", f"../../out/{snmp[j]}", "../../out/thefactory"])
                subprocess.run(["cp", f"../../out/{compute2[-1]}", "../../out/thefactory"])
        
    print("Running merger and columns hunter")
    subprocess.run(["python3", "../../out/thefactory/merger.py"]) 
    subprocess.run(["python3", "../../out/thefactory/columns_hunter.py"])

def return_mixed_part():
    print("Returning mixed part")
    def handleit(start, end, step, step_func, server):
        df_nodes = pd.read_csv("csv/nodes2.csv")
        json_h = {}

        for name, col in df_nodes.iterrows():
            query_name = col["query_name"]
            query = col["query"]
            try:
                instance = f'{return_instance("node", st_num=server)}'
            except:
                print("error")
                exit(1)

            url = curly_organizer(query, instance, step_func)
            url = organize_url(url, start, end, step)
            metric_data_node = rq.get(url).json()

            try:
                if len(metric_data_node['data']['result']) == 0:
                    print(f"No data for {query_name}")
                    continue
            except:
                print("Potential time error. Please check if start and end times relevant.")
                continue

            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])
            metric_data_node = metric_data_node[:,1].reshape(-1)
            metric_data_node = metric_data_node.astype(float)
            meann = np.mean(metric_data_node).round(4)
            json_h[query_name] = float(meann)
            print(f"Processed {query_name}: {meann}")
        
        print(f"Mixed part results: {json_h}")
        return json_h

    now = datetime.now()

    if now.second >= 30:
        start = now - timedelta(seconds=now.second, microseconds=now.microsecond)
        end = start + timedelta(seconds=30)
        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        print(f"Seconds >=30: start={start}, end={end}")
        return handleit(start, end, step, step_func, 0)
    else:
        start = now - timedelta(minutes=1, seconds=now.second, microseconds=now.microsecond) + timedelta(seconds=30)
        end = now - timedelta(seconds=now.second, microseconds=now.microsecond)
        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        print(f"Seconds <30: start={start}, end={end}")
        return handleit(start, end, step, step_func, 0)