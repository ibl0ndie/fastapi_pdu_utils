import pandas as pd
from organizer import *
import json
import requests as rq
import numpy as np
from settings import *
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from env import *


import aiohttp
_fastapi_app = None
def set_global_app(app):
    global _fastapi_app
    _fastapi_app = app
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

    return serv_dict


async def handle_aver_last_min2(server, last10=True, nmin=10):
    now = datetime.utcnow()
    start = now - timedelta(minutes=nmin)

    start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return await handleit2(start, end, step, step_func, server)


async def handleit2(start, end, step, step_func, server):
    df_nodes = pd.read_csv("nodes2.csv")
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
                continue
            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])[:, 1].astype(float)
            json_h[query_name] = float(np.mean(metric_data_node).round(4))
        except Exception as e:
            print(f"Error processing data: {e}")
            continue

    return json_h


async def fetch_json2(session, url):
    try:
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
#    string = string.replace("$", f'"{ip}"').replace("#", step_func)
#    return string

def organize_url2(query, start, end, step="5s"):
    url_str = query.replace("\"", "%22").replace("+", "%2B").replace("*", "%2A")
    return f"{prometheus_domain}/api/v1/query_range?query={url_str}&start={start}&end={end}&step={step}"


async def return_instance2(which="", start=give_default_dates()[0], end=give_default_dates()[1], st_num=0):
    async with aiohttp.ClientSession() as session:
        if which == "node":
            # assign query
            query = "node_load1"
            # load dates and query into URL
            url = f"http://localhost:9090/api/v1/query?query={query}&start={start}&end={end}&step=30s"
            
            # get data using aiohttp
            data= await fetch_json2(session,url)

            # parse data to get instance
            result = data['data']['result'][st_num]['metric']['instance']
            # return reached instance
            return f'"{result}"'

        elif which == "libvirt":
            # assign query
            query = "libvirt_domain_info_vstate"
            # load query and time data into URL
            url = f"http://localhost:9090/api/v1/query_range?query={query}&start={start}&end={end}&step=30s"
            
            # get data using aiohttp
            async with session.get(url) as response:
                data = await response.json()

            # parse data to get instance
            result = data['data']['result'][st_num]['metric']['instance']
            # return data
            return f'"{result}"'

        # if something goes wrong return error
        else:
            return -1





def handle_aver_last_min(server, last10=True, nmin=10, go_hour_back=None):
    
    now = datetime.now()
    start = now - timedelta(minutes=nmin) # datetime.timedelta(minutes=nmin)
    
    def handleit(start, end, step, step_func, server):

        df_nodes = pd.read_csv("nodes2.csv")
        execute_once = True
        json_h = {}

        for name, col in df_nodes.iterrows():

            # get queries and their names
            query_name = col["query_name"]
            query = col["query"]

            try:
                instance = f'{return_instance("node", st_num=server)}'
            except:
                print("error")
                exit(1)

            name_query = "node_uname_info{$}"

            url = curly_organizer(query, instance, step_func)

            # organize url(request) to prevent clutter
            url = organize_url(url, start, end, step)
            
            # get data using requests modul
            metric_data_node = rq.get(url).json()

            try:
                # check if there is node metric data
                if len(metric_data_node['data']['result']) == 0:
                    continue
            except:
                print("Potential time error. Please check if start and end times relevant.")
                continue
            
            # load metric data into a numpy array
            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])
            
            # print(metric_data_node[:,1].reshape(-1).shape)
            # print(metric_data_node)
            metric_data_node = metric_data_node[:,1].reshape(-1)
            metric_data_node = metric_data_node.astype(float)
            
            #print(type(np.mean(metric_data_node).round(4)))
            meann = np.mean(metric_data_node).round(4)
            json_h[query_name] = float(meann)
            # np.mean(metric_data_node).round(4) # np.mean(metric_data_node).round(4) # metric_data_node.mean()
        
        #print(json_h)
        return json_h

    if last10:

        
        now = datetime.now()
        start = now - timedelta(minutes=10) # datetime.timedelta(minutes=10)

        # 2023-08-28T12:47:00.000Z
        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        now = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ') # end

        if server or server == 0:
            # server = 0
            return handleit(start, now, step, step_func, server)
        else:
            server = 0
            filled_data = handleit(start, now, step, step_func, server)
            for i in filled_data.keys():
                filled_data[i] = 0

            return filled_data

    else:

        oncer = True

        if go_hour_back:
            
            now = datetime.now()

            for i in range(go_hour_back):
                end = now - timedelta(hours=i)
                start = now - timedelta(hours=i+1)

                end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                if oncer:
                    holder = pd.DataFrame(handleit(start, end, step, step_func, server), index=[0])
                    oncer = False
                else:
                    holder = pd.concat((holder, pd.DataFrame(handleit(start, end, step, step_func, server), index=[0])), axis=0)

            holder = holder.mean()
            json_data = holder.to_dict()
            # json_data_list = [{col: values[i] for col, values in json_data.items()} for i in range(len(holder))]

            # jsond = holder.to_dict(orient='records')

            return json_data

        else:

            now = datetime.now()
            start = now - timedelta(minutes=nmin)
            start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            now = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
            return handleit(start, now, step, step_func, server)


def get_actual_snmps_nmin(nmin):
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

        # once = True
        now = datetime.now()

        for elem in pdu_list:

        # data_arr = np.array(data['data']['result'][0]['values'])

        # data_arr = data_arr[:,1].reshape(-1)
        # data_arr = data_arr.astype(float)

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
        
        emp[i] = data_d

    return emp


def get_snmps_nmin(n, time_unit='m', compute_name='compute3'):

    end = datetime.now()
    
    req = rq.get('{prometheus_domain}/api/v1/query?query=pdu_power').json()
    compute_order = {}
    data_len = len(req['data']['result'])

    for i in range(data_len):
        compute_order[req['data']['result'][i]['metric']['compute_id']] = i
        
    if time_unit == 'm':

        start = end - timedelta(minutes=n)

        divisions = [[start, end]]

    if time_unit == 'h':
        start = end - timedelta(hours=n)
        # [[start, end]...]
        isOdd = i // 2 == 1
        # for 5: 0 2 2 4 4 5
        # start - end relative data

        divisions = [[end-timedelta(hours=2*i+2), end-timedelta(hours=(2*i))] for i in range(n // 2)]
        
        if isOdd:
            i = n // 2
            al =  [end-timedelta(hours=2*i+1), end-timedelta(hours=(2*i))]

            divisions.append(al)

    if time_unit == 'd':
        start = end - timedelta(hours=24*n)
        
        # for 5: 0 2 2 4 4 5
        # start - end relative data

        divisions = [[end-timedelta(hours=2*i+2), end-timedelta(hours=(2*i))] for i in range(n*12)]
    
    #print(divisions)
    once = True

    for subdiv in divisions:
        
        start = subdiv[0]
        end = subdiv[1]

        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
        pdu_list = ['pdu_power', 'pdu_energy', 'pdu_current', 'pdu_voltage', 'pdu_pf', 'time_stamp']
        data_d = {}
    
        # once = True
        now = datetime.now() 

        
        for elem in pdu_list:

        # data_arr = np.array(data['data']['result'][0]['values'])
        
        # data_arr = data_arr[:,1].reshape(-1)
        # data_arr = data_arr.astype(float)
        
            if elem == 'time_stamp':
                query = f"{prometheus_domain}/api/v1/query_range?query=pdu_pf&start={start}&end={end}&step=1s"
                data = rq.get(query).json()
                time_data = [i[0] for i in data['data']['result'][compute_order[compute_name]]['values']]
                data_d[elem] = time_data
            else:
                query = f"{prometheus_domain}/api/v1/query_range?query={elem}&start={start}&end={end}&step=1s"
                data = rq.get(query).json()
                data_arr = [i[1] for i in data['data']['result'][compute_order[compute_name]]['values']]
                data_d[elem] = data_arr
        
        if once:

            hold_df = pd.DataFrame(data=data_d, columns=pdu_list)
            once = False
        
        else:
            print('else')
            df = pd.DataFrame(data=data_d, columns=pdu_list)
            hold_df = pd.concat((hold_df, df), axis=0, ignore_index=True)
    
    def time_changer2(time):
        return datetime.fromtimestamp(time)

    # df['Date Time'] = pd.to_datetime(df['Date Time'])
    hold_df['time_stamp'] = hold_df.apply(lambda x: time_changer2(x['time_stamp']), axis=1)

    hold_df.to_csv(f'/home/ubuntu/myenv/myenv/{compute_name}.csv')

    return True


def get_snmps():
    
    data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_power").json()
    return data_js


def get_name_snmp():
    a = {i['metric']['compute_id']:i['value'][1] for i in get_snmps()['data']['result']}

    # data_js = rq.get("http://10.50.1.167:9090/api/v1/query?query=pdu_power").json()
    return a


def scraper_dict_cr():
    power_data_js, energy_data_js, current_data_js, voltage_data_js, pf_data_js = get_all_pdu_metrics()

    power = {i['metric']['compute_id']:i['value'][1] for i in power_data_js['data']['result']}
    voltage = {i['metric']['compute_id']:i['value'][1] for i in voltage_data_js['data']['result']}
    current = {i['metric']['compute_id']:i['value'][1] for i in current_data_js['data']['result']}
    pf = {i['metric']['compute_id']:i['value'][1] for i in pf_data_js['data']['result']}
    energy = {i['metric']['compute_id']:i['value'][1] for i in energy_data_js['data']['result']}
    
    empty = {"data": []}

    for i in power:
        print(i)
        print(power)
        a = {}

        if True:
            a["host"] = i
            a["power"] = power[i]
            a["voltage"] = voltage[i]
            a["current"] = current[i]
            a["pf"] = pf[i]
            a["energy"] = energy[i]

        empty["data"].append(a)

    return empty


def get_all_pdu_metrics():

    power_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_power").json()
    
    energy_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_energy").json()
    current_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_current").json()
    voltage_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_voltage").json()
    pf_data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=pdu_pf").json()

    return power_data_js, energy_data_js, current_data_js, voltage_data_js, pf_data_js


def get_ips():
    
    data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=node_load1").json()
    node_json = rq.get(f"{prometheus_domain}/api/v1/query?query=node_uname_info").json()
    
    # node_names = [x['nodename'] for x in node_json['data']['result']]
    
    serv_dict = {}
    ct = 0
    
    for nodename in node_json['data']['result']:
        nodename = nodename['metric']["instance"].split(':')[0]
        serv_dict[nodename] = ct

        ct += 1

    #for data in data_js['data']['result']:
    #    inst = data['metric']['instance']
    #    serv_dict[inst] = ct
    #
    #    ct += 1

    return serv_dict
        # dotsp = inst.split('.')
        # dotsp = dotsp[len(dotsp)-1]
        # dotsp = dotsp.split(":")[0]



def handle_auto_ip(serv_num):
    data_js = rq.get(f"{prometheus_domain}/api/v1/query?query=node_load1").json()
    
    ct = 0

    for data in data_js['data']['result']:
        inst = data['metric']['instance']
        dotsp = inst.split('.')
        dotsp = dotsp[len(dotsp)-1]
        dotsp = dotsp.split(":")[0]
        
        if serv_num == int(dotsp):
            print("---------------------------------------------------")
            return ct
            
        ct += 1
        
    
def return_cur(server):

    ifserv = False

    if server or server == 0:
        ifserv = True
    
    else:
        server = 0

    df_nodes = pd.read_csv("nodes2.csv")
    data = {}

    for name, col in df_nodes.iterrows():

        # get queries and their names
        query_name = col["query_name"]
        query = col["query"]
        
        instance = f'{return_instance("node", st_num=server)}'
        url = curly_organizer(query, instance, step_func)

        # apply server
        url = f'{prometheus_domain}/api/v1/query?query={url}'

        metric_data_node = rq.get(url).json()
        print(metric_data_node)

        try:
                # check if there is node metric data
            if len(metric_data_node['data']['result']) == 0:
                continue
        except:
            print("Potential time error. Please check if start and end times relevant.")
            continue

        # load metric data into a numpy array
        metric_data_node = np.array(metric_data_node['data']['result'][0]['value'])

        metric_data_node = metric_data_node[1].reshape(-1)
        metric_data_node = metric_data_node.astype(float)
        
        data[query_name] = float(metric_data_node.round(4))
    
    if ifserv:
        return data

    else:

        for key in data.keys():
            data[key] = 0
        
        return data

import subprocess


def organize_data(day):
     
    setting_file = open("/home/ubuntu/data_collector/prometheus-api-get-metric-data-main/src/settings.py", "w")
    setting_file.write(f"day = {day}\nhour = 0\nminute = 0\nsecond_in = 0\nstep = '2s'\nstep_func = '30s'\ndecimal_limit = 3\nlog = []")
    setting_file.close()

    subprocess.run(["python3", "/home/ubuntu/data_collector/prometheus-api-get-metric-data-main/src/main.py"])
    subprocess.run(["python3", "/home/ubuntu/out/edit.py"])
    # remove all in the factory
    subprocess.run(["python3", "/home/ubuntu/out/thefactory/remover.py"])

    proc = subprocess.Popen(["ls", "../../out"], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    exitcode = proc.returncode
    # list
    lslist = stdout.decode("utf-8").split('\n')[:-1]
    compute2 = []
    snmp = []

    for files in lslist:

        leng = len(files)
        ct = 0
        hold_file = ""

        for letters in files:
            if ct >leng-1:
                break
            
            hold_file += letters
            ct += 1

        files = hold_file

        if files[0:8] == "compute3":
            compute2.append(files)

        elif files[0:4] == "snmp":
            snmp.append(files)

    sns_times = []
    
    snmp_order_time = []

    for sns in snmp:
        time = sns[16:30]
        holl = ""
        for letters in time:
            if letters == "_":
                holl += " "
            elif letters == "T":
                holl += " "
            elif letters == ":":
                holl += " "
            elif letters == "-":
                holl += " "

            else:
                holl += letters
    
        # 1 2 are months and 4 5 are days, 7 8 are hour 10 11 are minutes 13 14 are seconds
        time = holl
        sns_times.append(time)
        #print(time)
    
        snmp_order_time.append(time)
    
    snmp_end_time = []
    for sns in snmp:
        time = sns[40:56]
        holl = ""
        for letters in time:
            if letters == "_":
                holl += " "
            elif letters == "T":
                holl += " "
            elif letters == ":":
                holl += " "
            elif letters == "-":
                holl += " "
            else:
                holl += letters
    
        # 1 2 are months and 4 5 are days, 7 8 are hour 10 11 are minutes 13 14 are seconds
        time = holl
        #print(time)
        #sns_times.append(time)
        #print(time)
        print(time)
        snmp_end_time.append(time)

    compute2_time = []
    #print(compute2)
    for elems in compute2:
        time = elems[20:34]
        #print(elems[15:29])
        holl = ""
    
        for letters in time:
            if letters == "_":
                holl += " "
            elif letters == "T":
                holl += " "
            #elif letters ==
            else:
                holl += letters
        hold = ""
        for letter in holl:
            if letter == "i":
                hold += " "
            else:
                hold += letter
        # 1 2 are months and 4 5 are days, 7 8 are hour 10 11 are minutes 13 14 are seconds
        time = hold
        #print(time)
        compute2_time.append(time)
    
    
    compute2_end = []
    #print(compute2)
    for elems in compute2:
        time = elems[47:61]
        #print(elems[15:29])
        holl = ""
    
        for letters in time:
            if letters == "_":
                holl += " "
            elif letters == "T":
                holl += " "
            #elif letters ==
            else:
                holl += letters
        hold = ""
        for letter in holl:
            if letter == "i":
                hold += " "
            else:
                hold += letter
        # 1 2 are months and 4 5 are days, 7 8 are hour 10 11 are minutes 13 14 are seconds
        time = hold
        print(time)
        compute2_end.append(time)
    
    now = datetime.now()
    start = now - timedelta(days=day) # datetime.timedelta(minutes=nmin)

    # for i in range(len(compute2_time)):
    if True:

        
        compute_start = compute2_time[len(compute2_time)-1]
        compute_start += " 2023"
        compute_start_datetime_obj = datetime.strptime(compute_start, "%m %d %H %M %S %Y")

        compute_end = compute2_end[len(compute2_time)-1]
        compute_end += " 2023"
        compute_end_datetime_obj = datetime.strptime(compute_end, "%m %d %H %M %S %Y")

        for j in range(len(snmp_order_time)):
            snmp_start = snmp_order_time[j]
            snmp_start += " 2023"
            # 09-20 21:10:09 2023
            print(snmp_start)
            # print(snmp_end)
            snmp_start_datetime_obj = datetime.strptime(snmp_start, "%m %d %H %M %S %Y")

            snmp_end = snmp_end_time[j]
            snmp_end += " 2023"
            print(snmp_end)
            snmp_end_datetime_obj = datetime.strptime(snmp_end, "%m %d %H %M %S %Y")
            
            if (snmp_start_datetime_obj>=compute_start_datetime_obj and snmp_start_datetime_obj<=compute_end_datetime_obj) or (snmp_end_datetime_obj>=compute_start_datetime_obj and snmp_end_datetime_obj<=compute_end_datetime_obj):
            # if (snmp_start>=compute_start and snmp_end>=compute_end) or (snmp_start>=compute_start and snmp_end<=compute_end)
            # if (snmp_start<compute_end or snmp_start>compute_start) or (snmp_end>compute_start or snmp_end<compute_end):
                subprocess.run(["cp", f"../../out/{snmp[j]}", "../../out/thefactory"])
                subprocess.run(["cp", f"../../out/{compute2[len(compute2_time)-1]}", "../../out/thefactory"])
        
    # columns_hunter.py  merger.py
    subprocess.run(["python3", "../../out/thefactory/merger.py"]) 
    subprocess.run(["python3", "../../out/thefactory/columns_hunter.py"])

# organize_data(1)

def return_mixed_part():

    def handleit(start, end, step, step_func, server):

        df_nodes = pd.read_csv("nodes2.csv")
        execute_once = True
        json_h = {}

        for name, col in df_nodes.iterrows():

            # get queries and their names
            query_name = col["query_name"]
            query = col["query"]

            try:
                instance = f'{return_instance("node", st_num=server)}'
            except:
                print("error")
                exit(1)

            name_query = "node_uname_info{$}"

            url = curly_organizer(query, instance, step_func)

            # organize url(request) to prevent clutter
            url = organize_url(url, start, end, step)

            # get data using requests modul
            metric_data_node = rq.get(url).json()

            try:
                # check if there is node metric data
                if len(metric_data_node['data']['result']) == 0:
                    continue
            except:
                print("Potential time error. Please check if start and end times relevant.")
                continue

            # load metric data into a numpy array
            metric_data_node = np.array(metric_data_node['data']['result'][0]['values'])

            # print(metric_data_node[:,1].reshape(-1).shape)
            # print(metric_data_node)
            metric_data_node = metric_data_node[:,1].reshape(-1)
            metric_data_node = metric_data_node.astype(float)

            #print(type(np.mean(metric_data_node).round(4)))
            meann = np.mean(metric_data_node).round(4)
            json_h[query_name] = float(meann)
            # np.mean(metric_data_node).round(4) # np.mean(metric_data_node).round(4) # metric_data_node.mean()

        print(json_h)
        return json_h

    now = datetime.now()

    if now.second>=30:

        start = now - timedelta(seconds=now.second, microseconds=now.microsecond) # datetime.timedelta(minutes=10)
        end = now - timedelta(seconds=now.second, microseconds=now.microsecond) + timedelta(seconds=30) # datetime.timedelta(minutes=10)

        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        print("larger30: ", start, end)
        nw = handleit(start, end, step, step_func, 0)
        # nw["end"] = end
        return nw # handleit(start, end, step, step_func, 0)

    else:

        start = now - timedelta(microseconds=now.microsecond, minutes=1, seconds=now.second) + timedelta(seconds=30) 
        # datetime.timedelta(minutes=10)

        end = now - timedelta(microseconds=now.microsecond, seconds=now.second) # datetime.timedelta(minutes=10)

        start = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        print("lower 30: ", start, end)
        nw = handleit(start, end, step, step_func, 0)
        # nw["end"] = end
        return nw # handleit(start, end, step, step_func, 0)

