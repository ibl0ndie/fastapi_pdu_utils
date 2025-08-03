from fastapi import FastAPI, Response
from datetime import datetime
import subprocess
import time

app = FastAPI()

# --- Define compute mapping and OIDs dynamically ---
COMPUTES = [
    {
        "id": "compute1",
        "current_oid": "1.3.6.1.4.1.42578.1.3.2.3.0",  # socket 2
        "voltage_oid": "1.3.6.1.4.1.42578.1.2.2.0",    # shared voltage
        "energy_oid": "1.3.6.1.4.1.42578.1.2.5.0",     # shared energy
        "pf_oid": None 
    },
    {
        "id": "compute2",
        "current_oid": "1.3.6.1.4.1.42578.1.3.4.3.0",  # socket 4
        "voltage_oid": "1.3.6.1.4.1.42578.1.2.2.0",
        "energy_oid": "1.3.6.1.4.1.42578.1.2.5.0",
        "pf_oid": None
    },
    {
        "id": "compute3",
        "current_oid": "1.3.6.1.4.1.42578.1.3.6.3.0",  # socket 6
        "voltage_oid": "1.3.6.1.4.1.42578.1.2.2.0",
        "energy_oid": "1.3.6.1.4.1.42578.1.2.5.0",
        "pf_oid": None
    },
    {
        "id": "compute4",
        "current_oid": "1.3.6.1.4.1.42578.1.3.8.3.0",  # socket 8
        "voltage_oid": "1.3.6.1.4.1.42578.1.2.2.0",
        "energy_oid": "1.3.6.1.4.1.42578.1.2.5.0",
        "pf_oid": None
    }
]


# --- Data parsing functions ---
def spl_current(data):
    return 0.001 * int(data.split(':')[1])

def spl_int(data):
    return 0.01 * int(data.split(':')[1])

def spl_energy(data):
    return 10 * int(data.split(':')[1])  # Convert from KWh to Wh


# --- SNMP query helper ---
def snmp_get(pdu_ip, oid):
    result = subprocess.Popen(
        ["snmpget", "-v1", "-c", "public", pdu_ip, oid],
        stdout=subprocess.PIPE
    ).communicate()[0].decode("utf-8")
    return result


# --- Main sensor reading logic ---
def get_sensor_data():
    pdu_ip = "10.150.1.78"
    start = time.time()

    result_lines = []

    total_current = 0.0
    compute_data = []

    # --- First pass: retrieve current and voltage per compute ---
    for compute in COMPUTES:
        cid = compute["id"]

        try:
            current = spl_current(snmp_get(pdu_ip, compute["current_oid"]))
            voltage = spl_int(snmp_get(pdu_ip, compute["voltage_oid"]))
            energy = spl_energy(snmp_get(pdu_ip, compute["energy_oid"]))
        except Exception as e:
            print(f"[Error] SNMP fetch failed for {cid}: {e}")
            continue

        power = round(current * voltage, 3)
        compute_data.append({
            "id": cid,
            "current": current,
            "voltage": voltage,
            "energy": energy,
            "power": power,
            "pf": 0.0
        })

        total_current += current

    # --- Optional: Add current-based proportional energy if needed ---
    for data in compute_data:
        prop = data["current"] / total_current if total_current else 0
        data["energy_proportional"] = round(data["energy"] * prop, 3)

    # --- Format output ---
    for data in compute_data:
        result_lines.append(f'pdu_power{{compute_id="{data["id"]}"}} {data["power"]}')
        result_lines.append(f'pdu_voltage{{compute_id="{data["id"]}"}} {data["voltage"]}')
        result_lines.append(f'pdu_current{{compute_id="{data["id"]}"}} {data["current"]}')
        result_lines.append(f'pdu_energy{{compute_id="{data["id"]}"}} {data["energy_proportional"]}')
        result_lines.append(f'pdu_pf{{compute_id="{data["id"]}"}} {data["pf"]}')

    end = time.time()
    print(f"[INFO] SNMP scrape completed in {round(end - start, 2)} seconds")

    return "\n".join(result_lines)


# --- FastAPI route ---
@app.get("/metrics")
async def metrics():
    sensor_data = get_sensor_data()
    print("[INFO] /metrics request at", datetime.now())
    return Response(sensor_data, media_type="text/plain")


# --- Optional: local run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
