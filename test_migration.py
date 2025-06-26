api_key = "4QGEF_nKKnmyrsQyh3wqvvqOfgZO5pfrPTBPKi8uXFI="
instance_name = "aypostest10"

header = {"X-Auth-Key": api_key}

import requests as rq
import json

mig_req = {"vm_name": "aypostest10", "to_host": "compute4"}

resp = rq.post("http://10.150.1.30:5001/migrate", json=str(mig_req), headers=header)
# print(resp.text)
print(resp.status_code)
print(resp.json())
