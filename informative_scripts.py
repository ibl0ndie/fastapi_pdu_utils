
script_phy_mac = """
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

script_vm_mac_details = '''
from openstack import connection
import os

# OpenStack kimlik bilgilerinizi ayarlayýn

auth_url = "http://10.150.1.251:35357/v3"
project_name = "admin"
username = "admin"
password = "WHMFjzLBHf1N6FxPnZpCDsXYdXewgjsvwju385Mk"
user_domain_name = "Default"
project_domain_name ="Default"


# OpenStack ortamýna baðlantý oluþturun
conn = connection.Connection(
    auth_url=auth_url,
    project_name=project_name,
    username=username,
    password=password,
    user_domain_name=user_domain_name,
    project_domain_name=project_domain_name,
)

# Sanal makineler (örnekler) hakkýnda bilgi alýn
def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances



def get_vm_by_id(vm_id):

    compute_service = conn.compute
    try:
        vm = compute_service.get_server(vm_id)

        flav = vm.flavor.copy()

        flav["host"] = vm.compute_host
        #flav['compute_host'] = vm.compute_host
        asd = vm.addresses.copy()

        flav["ip"] = asd["Internal"][1]["addr"]

        return vm.name, flav

    except Exception as e:
        print(f"Error retrieving VM with ID {vm_id}: {e}")
        return None


def get_flavors():

    data = {}
    virtual_machines = get_virtual_machines()

    for vm in virtual_machines:
        name, flavor = get_vm_by_id(vm.id)

        data[name] = flavor

    return {"result": data}


print(get_flavors())

'''

script_pm_mac_details = '''

import subprocess


def get_host_list():
    output = subprocess.run(['openstack', 'hypervisor', 'list'], capture_output=True, text=True).stdout

    rows = output.strip().split("\n
            ")[2:]

    indexes = []

    for row in rows:

        splitted = row.split('|')

        if len(splitted)>1:
            indexes.append(splitted[1].replace(" ", ""))

    return indexes
    

def get_host_details(index):
    # Execute the command and capture output
    output = subprocess.run(['openstack', 'hypervisor', 'show', str(index)], capture_output=True, text=True).stdout
    #print(output)
    # Process lines containing relevant data (modify as needed)
    data = {}

    for line in output.strip().split("\n"):

        splitted = line.split("|")

        if len(splitted) < 2:
            continue

        wout0 = splitted[1].replace(" ", "")
        wout1 = splitted[2].replace(" ", "")

        if wout0 == "aggregates":
            wout1 = wout1[2:len(wout1)-2]
            data[wout0] = wout1

        elif wout0 in ["vcpus", "memory_mb", "aggregates", "host_ip", "local_gb", "hypervisor_hostname"]:
            data[wout0] = wout1

    return data


print_data = {}

for i in get_host_list():

    details = get_host_details(i)

    if details:
        print_data[details["hypervisor_hostname"]] = details


print(print_data)

'''

comp_vm = '''
from openstack import connection
import os

# OpenStack kimlik bilgilerinizi ayarlayýn

auth_url = "http://10.150.1.251:35357/v3"
project_name = "admin"
username = "admin"
password = "WHMFjzLBHf1N6FxPnZpCDsXYdXewgjsvwju385Mk"
user_domain_name = "Default"
project_domain_name ="Default"


# OpenStack ortamýna baðlantý oluþturun
conn = connection.Connection(
    auth_url=auth_url,
    project_name=project_name,
    username=username,
    password=password,
    user_domain_name=user_domain_name,
    project_domain_name=project_domain_name,
)

# Sanal makineler (örnekler) hakkýnda bilgi alýn
def get_virtual_machines():
    compute_service = conn.compute
    instances = compute_service.servers()
    return instances


def get_vm_by_id(vm_id):

    compute_service = conn.compute
    try:
        vm = compute_service.get_server(vm_id)
        return vm.name, vm.compute_host

    except Exception as e:
        print(f"Error retrieving VM with ID {vm_id}: {e}")
        return None


def get_flavors():

    virtual_machines = get_virtual_machines()
    con_cd = {}
    lat = {"data": []}
    for vm in virtual_machines:
        name, compute = get_vm_by_id(vm.id)

        if compute in con_cd.keys():
            con_cd[compute].append(name)
        else:
            con_cd[compute] = []

    for i in con_cd:
        lat["data"].append({"virtual_machines": con_cd[i], "host": i})

    return lat


print(get_flavors())

'''
