from reach_time import *
import numpy as np

# organizes the query, selects and returns query
def curly_organizer(string, ip,step_func="5m"):

    # create a string to return
    hold_str = ""

    # look at letters one by one and organize
    for letter in string:
        if letter == "$":
            hold_str += ip

        elif letter == "#":
            hold_str += step_func
        # adds letters that are not in curly branches
        else:

            hold_str += letter

    # return the hold_str string after performing step choice of some query functions
    return hold_str


# organizes the URL and fixes URL request errors
# do it because sometimes it makes problem of request
def organize_url(query, start, end, step="5s"):
    # define a string to order and return
    url_str = ""
    # get some chars which create problems,
    # change them to URL utf-8 characters
    for letter in query:
        # if there is (") character, change it to "%22"
        if letter == "\"":
            url_str += "%22"
        # if there is "+" character, change it to "%2B"
        elif letter == "+":
            url_str += "%2B"
        # if there is "*" character, change it to %2A
        elif letter == "*":
            url_str += "%2A"

        #        elif letter=="-":
        #            url_str+="%2D"
        # if there is no character which we search, don't change and add
        else:
            url_str += letter

    # return ordered string-url
    url_str = f"http://localhost:9090/api/v1/query_range?query={url_str}&start={start}&end={end}&step={step}"
    return url_str


# a function to reach domain names gets recent time data
def reach_device(start=give_default_dates()[0], end=give_default_dates()[1]):
    # define an empty list
    domains = []
    # define a query
    query = "libvirt_domain_info_vstate"
    # load the query and the taken time data into an URL
    url = f"http://localhost:9090/api/v1/query_range?query={query}&start={start}&end={end}&step=3m"

    # get data using api
    data = rq.get(url)
    # turn data into a dictionary
    data = data.json()
    # data = json.dumps(data, indent=4)

    # parse into the data, reach machine names
    for i in (range(len(data["data"]["result"]))):
        hold = data["data"]["result"][i]["metric"]["domain"]
        # add machine names into defined empty-list
        domains.append(hold)

    # return domain names(virtual machine names)
    return domains


def uptime_decoder(second):

    day = int(second / (24*60*60))
    hour = int((second-day*24*60*60) / (60*60))+day*24
    minute = int((second-day*24*60*60-hour*60*60)/60)
    ot_second = int(second-day*24*60*60-hour*60*60-minute*60)
    return day, hour, minute, ot_second


# improve it
def time_div_step(day, hour, minute,second, step):

    total_sec = 0
    total_sec += day*24*60*60
    total_sec += hour*60*60
    total_sec += minute*60
    total_sec += second

    divider = int(total_sec / (11000*step)) +1

    # while data number is smaller than 11.000(10800 was set up because of such a nice number)
    # define a divider and act based on it.
    sec_over_per = int(total_sec/divider)
    if (total_sec%divider!=0):
        sec_over_per += 1

    fir, sec, thi, fou = uptime_decoder(sec_over_per)
    # go into here and step variable
    return fir,sec,thi,fou, divider
    #return uptime_decoder(int(total_sec/divider)), divider

def return_instance(which="", start=give_default_dates()[0], end=give_default_dates()[1],st_num=0):

    if which == "node":
        # assign query
        query = "node_load1"
        # load dates and query into URL
        url = f"http://localhost:9090/api/v1/query?query={query}&start={start}&end={end}&step=30s"

        # get data using requests
        data = rq.get(url)
        # turn data into dictionary
        data = data.json()

        # parse data to get instance
        result = data['data']['result'][st_num]['metric']['instance']
        # return reached instance
        return f'"{result}"'

    elif which == "libvirt":
        # assign query
        query = "libvirt_domain_info_vstate"
        # load query and time data into URL
        url = f"http://localhost:9090/api/v1/query_range?query={query}&start={start}&end={end}&step=30s"

        # get data using requests library
        data = rq.get(url)
        # turn data into dictionary to be able to pars
        data = data.json()

        # parse data to get instance
        result = data['data']['result'][st_num]['metric']['instance']

        # return data
        return f'"{result}"'

    # if something goes wrong return error
    else:
        return -1


def give_len(start=give_default_dates()[0], end=give_default_dates()[1]):
    len_node, len_libv = 0, 0
    try:
        # assign query
        query = "node_load1"
        # load dates and query into URL
        url = f"http://localhost:9090/api/v1/query?query={query}&start={start}&end={end}&step=30s"

        # get data using requests
        data = rq.get(url)
        # turn data into dictionary
        datanode = data.json()
        len_node = len(datanode['data']['result'])

        # assign query
        query = "libvirt_domain_info_vstate"
        # load query and time data into URL
        url = f"http://localhost:9090/api/v1/query_range?query={query}&start={start}&end={end}&step=30s"

        # get data using requests library
#        data = rq.get(url)
        # turn data into dictionary to be able to pars
#        data = data.json()
#        len_libv = len(data['data']['result'])

    except:
        pass

    return len_node, len_libv


def fill_up_buffer_err(arr, size):
    # give metric_ll
    a = (np.array([0,1])[0])
    if int(arr.shape[0]) == int(size):
        return arr

    arr = np.append(arr, a)
    print(arr.shape[0])
    return fill_up_buffer_err(arr,size)
    #return fill_up_buffer_err(arr, size)

