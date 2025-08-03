import subprocess
import psutil
from openstack import connection

# ======================
# PHYSICAL MACHINE DETAILS
# ======================
def get_physical_machine_details():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_count = psutil.cpu_count()

    # Calculate memory metrics
    total_memory = memory.total / (1024 ** 3)
    available_memory = memory.available / (1024 ** 3)
    used_memory = memory.used / (1024 ** 3)
    free_memory = memory.free / (1024 ** 3)

    # Calculate disk metrics
    disk_total = disk.total / (1024 ** 3)
    disk_used = disk.used / (1024 ** 3)
    disk_free = disk.free / (1024 ** 3)

    # Prepare values and names
    values = [
        f"{cpu_count:.2f}", 
        f"{total_memory:.3f}", 
        f"{available_memory:.3f}", 
        f"{used_memory:.3f}", 
        f"{free_memory:.3f}", 
        f"{disk_total:.3f}", 
        f"{disk_used:.3f}", 
        f"{disk_free:.3f}"
    ]
    
    names = [
        "cpu_count",
        "total_memory(GB)",
        "available_memory(GB)",
        "used_memory(GB)",
        "free_memory(GB)",
        "disk_total(GB)",
        "disk_used(GB)",
        "disk_free(GB)"
    ]

    # Format output message
    message_parts = []
    for i in range(len(values)):
        message_parts.append(f"{names[i]}-{values[i]}")
    
    return "/".join(message_parts)


# ======================
# OPENSTACK CONNECTION
# ======================
def create_openstack_connection():
    return connection.Connection(
        auth_url="http://10.150.1.251:35357/v3",
        project_name="admin",
        username="admin",
        password="WHMFjzLBHf1N6FxPnZpCDsXYdXewgjsvwju385Mk",
        user_domain_name="Default",
        project_domain_name="Default",
    )


# ======================
# VIRTUAL MACHINE DETAILS
# ======================
def get_virtual_machines(conn):
    return conn.compute.servers()

def get_vm_details(vm_id, conn):
    try:
        vm = conn.compute.get_server(vm_id)
        flavor = vm.flavor.copy()
        flavor["host"] = vm.compute_host
        
        if "Internal" in vm.addresses:
            flavor["ip"] = vm.addresses["Internal"][1]["addr"]
        
        return vm.name, flavor
    except Exception as e:
        print(f"Error retrieving VM with ID {vm_id}: {e}")
        return None, None

def get_all_vm_details():
    conn = create_openstack_connection()
    virtual_machines = get_virtual_machines(conn)
    result = {}
    
    for vm in virtual_machines:
        name, flavor = get_vm_details(vm.id, conn)
        if name and flavor:
            result[name] = flavor
    
    return {"result": result}


# ======================
# HYPERVISOR DETAILS
# ======================
def get_hypervisor_list():
    output = subprocess.run(
        ['openstack', 'hypervisor', 'list'], 
        capture_output=True, 
        text=True
    ).stdout
    
    rows = output.strip().split("\n")[3:]
    indexes = []
    
    for row in rows:
        parts = row.split('|')
        if len(parts) > 2:
            indexes.append(parts[1].strip())
    
    return indexes

def get_hypervisor_details(index):
    output = subprocess.run(
        ['openstack', 'hypervisor', 'show', str(index)], 
        capture_output=True, 
        text=True
    ).stdout
    
    data = {}
    
    for line in output.strip().split("\n"):
        parts = line.split("|")
        if len(parts) < 3:
            continue
            
        key = parts[1].strip()
        value = parts[2].strip()
        
        if key == "aggregates":
            data[key] = value[1:-1]  # Remove brackets
        elif key in ["vcpus", "memory_mb", "host_ip", "local_gb", "hypervisor_hostname"]:
            data[key] = value
    
    return data

def get_all_hypervisor_details():
    hypervisors = {}
    
    for index in get_hypervisor_list():
        details = get_hypervisor_details(index)
        if details and "hypervisor_hostname" in details:
            hypervisors[details["hypervisor_hostname"]] = details
    
    return hypervisors


# ======================
# VM PER HYPERVISOR
# ======================
def get_vms_per_hypervisor():
    conn = create_openstack_connection()
    virtual_machines = get_virtual_machines(conn)
    vm_host_mapping = {}
    
    for vm in virtual_machines:
        name, host = get_vm_and_host(vm.id, conn)
        if host:
            vm_host_mapping.setdefault(host, []).append(name)
    
    result = {"data": []}
    for host, vms in vm_host_mapping.items():
        result["data"].append({"virtual_machines": vms, "host": host})
    
    return result

def get_vm_and_host(vm_id, conn):
    try:
        vm = conn.compute.get_server(vm_id)
        return vm.name, vm.compute_host
    except Exception as e:
        print(f"Error retrieving VM with ID {vm_id}: {e}")
        return None, None


# ======================
# MAIN EXECUTION
# ======================
if __name__ == "__main__":
    # Physical machine details
    print("Physical Machine Details:")
    print(get_physical_machine_details())
    
    # Virtual machine details
    print("\nVirtual Machine Details:")
    print(get_all_vm_details())
    
    # Hypervisor details
    print("\nHypervisor Details:")
    print(get_all_hypervisor_details())
    
    # VMs per hypervisor
    print("\nVMs per Hypervisor:")
    print(get_vms_per_hypervisor())