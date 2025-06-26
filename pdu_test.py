from fastapi import FastAPI, Response
import subprocess
import time
import yaml

app = FastAPI()

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def snmp_get(oid: str, ip: str) -> str:
    try:
        result = subprocess.check_output(
            ["snmpget", "-v1", "-c", "public", ip, oid],
            stderr=subprocess.DEVNULL
        ).decode()
        return result.split(":", 1)[-1].strip()
    except subprocess.CalledProcessError:
        return "ERROR:0"

def parse_value(snmp_output: str) -> float:
    try:
        return float(snmp_output.split()[-1])
    except Exception:
        return 0.0

@app.get("/")
def export_metrics():
    config = load_config()
    pdu_ip = config["pdu"]["ip"]
    voltage = parse_value(snmp_get(config["pdu"]["voltage_oid"], pdu_ip))
    energy = parse_value(snmp_get(config["pdu"]["energy_oid"], pdu_ip))

    start = time.time()
    metrics = []

    for server in config["pdu"]["servers"]:
        current = parse_value(snmp_get(server["current_oid"], pdu_ip))
        power = round(current * voltage, 2)

        metrics.append(f'pdu_current{{compute_id="{server["name"]}"}} {current}')
        metrics.append(f'pdu_power{{compute_id="{server["name"]}"}} {power}')

    metrics.append(f'pdu_voltage {voltage}')
    metrics.append(f'pdu_energy {energy}')
    metrics.append(f'pdu_script_duration_seconds {round(time.time() - start, 3)}')

    return Response("\n".join(metrics), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9099)
