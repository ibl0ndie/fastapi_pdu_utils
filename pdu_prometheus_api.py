from fastapi import FastAPI, Response
from datetime import datetime
import subprocess

app = FastAPI()


def spl(data):
    return 0.01 * int(data.split(':')[1])

"""

def split_string(data):
    print(data)
    seperator="\""
    
    parts = data.split(seperator,1)
    print(parts)
    return tuple(parts)

def spl_int(data):
    print(data)
    num = float(data.split(":")[1])
    return num

def spl (data):
    print(data)
    test = split_string(data)[1]
    print(test)
    test2 = split_string(test)[0]
    return test2
"""


def spl_current(data):
    return 0.001 * int(data.split(':')[1])


def spl_int(data):
    print(data.split(':'))
    return 0.01 * int(data.split(':')[1])


def spl_energy(data):
    return  10 * int(data.split(':')[1])   # Wh from KWh
import time


def get_sensor_data():
    start = time.time()
    pdu_ip = "10.150.1.78"
    
    # voltage_1_12 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.3.1.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # voltage_1_12 = float(spl(voltage_1_12))
 
    # voltage_13_24 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.3.2.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # voltage_13_24 = float(spl(voltage_13_24))

    # curr_compute4 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.8.1.21.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # curr_compute4 = float(spl(curr_compute4))

    # curr_compute3 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.8.1.6.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # curr_compute3 = float(spl(curr_compute3))

    # curr_compute
    # curr_compute1 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.8.1.4.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # curr_compute1 = float(spl(curr_compute1))

    # curr_compute2 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.8.1.10.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

    # energy_1_12 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.3.1.5.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

    # energy_13_24 = subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.3.2.5.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    

    def snmp_get(oid):
        return subprocess.Popen([
            r"snmpget", "-v1", "-c", "public", pdu_ip, oid
        ], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

    # Retrieve voltages
    print(snmp_get("1.3.6.1.4.1.42578.1.2.2.0"))

    voltage_1_12 = float(spl_int(snmp_get("1.3.6.1.4.1.42578.1.2.2.0"))) # float(spl(snmp_get("iso.3.6.1.4.1.30966.5.1.1.3.5.0")))
    voltage_13_24 = voltage_1_12
    # Retrieve currents

    spl = spl_current  # just change function object

    # !!!!!!!!!!!

    # remove *2 after using just 1 cable connected to the servers !!!!!!

    #!!!!!!!!!!!
    curr_compute1 = float(spl(snmp_get("1.3.6.1.4.1.42578.1.3.2.3.0")))  # Socket 2
    curr_compute2 = float(spl(snmp_get("1.3.6.1.4.1.42578.1.3.4.3.0")))  # Socket 4
    curr_compute3 = float(spl(snmp_get("1.3.6.1.4.1.42578.1.3.6.3.0")))  # Socket 6
    curr_compute4 = float(spl(snmp_get("1.3.6.1.4.1.42578.1.3.8.3.0")))  # Socket 8

    # Retrieve energies
    # turn into kwh????  
    energy_1_12 = float(spl_energy(snmp_get("1.3.6.1.4.1.42578.1.2.5.0"))) # float(spl(snmp_get("iso.3.6.1.4.1.30966.5.1.1.3.9.0")))
    energy_13_24 = energy_1_12 # float(spl(snmp_get("iso.3.6.1.4.1.30966.7.1.3.2.5.0")))

    # Compute proportions and energies per component
    total_curr_1_12 = curr_compute1 + curr_compute2 + curr_compute3
    currprop1 = curr_compute1 / total_curr_1_12
    currprop2 = curr_compute2 / total_curr_1_12
    currprop3 = curr_compute3 / total_curr_1_12

    curr_compute2 = float(curr_compute2)

    energy_1_12 = float(energy_1_12)
    energy_13_24 = float(energy_13_24)

    total_curr_1_12 = curr_compute1 + curr_compute2 + curr_compute3
    currprop1 = curr_compute1 / total_curr_1_12 
    currprop2 = curr_compute2 / total_curr_1_12
    currprop3 = curr_compute3 / total_curr_1_12
    
    energy_comp1 = currprop1 * energy_1_12
    energy_comp2 = currprop2 * energy_1_12
    energy_comp3 = currprop3 * energy_1_12
    energy_comp4 = energy_13_24

    pf_compute1 =  0 # subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"1.3.6.1.4.1.42578.1.3.2.5"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute1 = 0 # float(spl(pf_compute1))

    pf_compute2 = pf_compute1 # subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.9.10.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute2 = pf_compute1 # float(spl(pf_compute2))

    pf_compute3 = pf_compute1 # subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.9.6.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute3 = pf_compute1 # float(spl(pf_compute3))

    pf_compute4 = pf_compute1 # subprocess.Popen([r"snmpget","-v1","-c","public",pdu_ip,"iso.3.6.1.4.1.30966.7.1.9.21.0"], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    pf_compute4 = pf_compute1 # float(spl(pf_compute4))

    end = time.time() 

    print('time takes: ', end-start)
    return (f'pdu_power{{compute_id="compute1"}} {round(curr_compute1*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute2"}} {round(curr_compute2*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute3"}} {round(curr_compute3*voltage_1_12, 3)}\n'
            f'pdu_power{{compute_id="compute4"}} {round(curr_compute4*voltage_13_24, 3)}\n'
            f'pdu_pf{{compute_id="compute1"}} {pf_compute1}\n'
            f'pdu_pf{{compute_id="compute2"}} {pf_compute2}\n'
            f'pdu_pf{{compute_id="compute3"}} {pf_compute3}\n'
            f'pdu_pf{{compute_id="compute4"}} {pf_compute4}\n'
            f'pdu_current{{compute_id="compute1"}} {curr_compute1}\n'
            f'pdu_current{{compute_id="compute2"}} {curr_compute2}\n'
            f'pdu_current{{compute_id="compute3"}} {curr_compute3}\n'
            f'pdu_current{{compute_id="compute4"}} {curr_compute4}\n'
            f'pdu_energy{{compute_id="compute1"}} {energy_comp1}\n'
            f'pdu_energy{{compute_id="compute2"}} {energy_comp2}\n'
            f'pdu_energy{{compute_id="compute3"}} {energy_comp3}\n'
            f'pdu_energy{{compute_id="compute4"}} {energy_comp4}\n'
            f'pdu_voltage{{compute_id="compute1"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute2"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute3"}} {voltage_1_12}\n'
            f'pdu_voltage{{compute_id="compute4"}} {voltage_13_24}\n')

@app.get("/metrics")
async def metrics():
    sensor_data = get_sensor_data()
    print('request: ',  datetime.now())

    return Response(sensor_data, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)

