import requests as rq

def handle_auto_ip(serv_num):
    data_js = rq.get("http://10.150.1.167:9090/api/v1/query?query=node_load1").json()
    print(data_js)
    
handle_auto_ip(1)
