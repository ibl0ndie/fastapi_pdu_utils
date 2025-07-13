import numpy as np
import requests as rq
from reach_time import give_default_dates

# ======================
# QUERY PROCESSING UTILITIES
# ======================

def curly_organizer(string, ip, step_func="5m"):
    """
    Replaces placeholder characters in query strings with actual values.
    
    Args:
        string: The original query template string
        ip: The IP address to replace '$' placeholders
        step_func: The step value to replace '#' placeholders (default "5m")
    
    Returns:
        Modified query string with placeholders replaced
    """
    # Replace $ with IP and # with step function value
    return string.replace("$", ip).replace("#", step_func)


def organize_url(query, start, end, step="5s"):
    """
    Encodes special characters in Prometheus queries and constructs full API URL.
    
    Args:
        query: The Prometheus query string
        start: Start time in ISO 8601 format
        end: End time in ISO 8601 format
        step: Query resolution step width (default "5s")
    
    Returns:
        Fully formatted and encoded Prometheus API URL
    """
    # URL-encode special characters that cause issues in API requests
    encoded_query = (
        query.replace('\"', '%22')  # Double quote
             .replace('+', '%2B')   # Plus sign
             .replace('*', '%2A')   # Asterisk
    )
    
    # Construct full API endpoint URL
    return (
        f"http://localhost:9090/api/v1/query_range?"
        f"query={encoded_query}&start={start}&end={end}&step={step}"
    )


# ======================
# TIME PROCESSING UTILITIES
# ======================

def uptime_decoder(seconds):
    """
    Converts total seconds into a time decomposition of days, hours, minutes, seconds.
    
    Args:
        seconds: Total number of seconds to decompose
    
    Returns:
        Tuple of (days, hours, minutes, seconds)
    """
    # Calculate days and remaining seconds
    days, rem = divmod(seconds, 86400)  # 24*60*60
    # Calculate hours and remaining seconds
    hours, rem = divmod(rem, 3600)     # 60*60
    # Calculate minutes and seconds
    minutes, seconds = divmod(rem, 60)
    
    return int(days), int(hours), int(minutes), int(seconds)


def time_div_step(days, hours, minutes, seconds, step):
    """
    Calculates time segmentation to keep data points under 11,000 limit.
    
    Args:
        days: Days component of time range
        hours: Hours component of time range
        minutes: Minutes component of time range
        seconds: Seconds component of time range
        step: Time between data points in seconds
    
    Returns:
        Tuple of (segment_days, segment_hours, segment_minutes, segment_seconds, divider)
    """
    # Convert all time components to total seconds
    total_seconds = days*86400 + hours*3600 + minutes*60 + seconds
    
    # Prometheus has a limit of ~11,000 data points per query
    max_points = 11000
    
    # Calculate how many segments we need to divide the time range into
    divider = max(1, total_seconds // (max_points * step) + 1)
    
    # Calculate seconds per segment using ceiling division
    segment_seconds = (total_seconds + divider - 1) // divider
    
    # Return decomposed time and divider count
    return (*uptime_decoder(segment_seconds), divider


# ======================
# PROMETHEUS API INTERACTION
# ======================

def reach_device(start=None, end=None):
    """
    Retrieves list of virtual machine domains from Prometheus metrics.
    
    Args:
        start: Start time in ISO format (defaults to current time - 1 hour)
        end: End time in ISO format (defaults to current time)
    
    Returns:
        List of domain names or empty list on error
    """
    # Set default time range if not provided
    start = start or give_default_dates()[0]
    end = end or give_default_dates()[1]
    
    # Construct API URL for libvirt domain info
    url = (
        f"http://localhost:9090/api/v1/query_range?"
        f"query=libvirt_domain_info_vstate&start={start}&end={end}&step=3m"
    )
    
    try:
        # Execute API request with timeout
        response = rq.get(url, timeout=5)
        # Parse JSON response
        data = response.json()
        # Extract domain names from result metrics
        return [result["metric"]["domain"] for result in data["data"]["result"]]
    except Exception:
        # Return empty list on any error
        return []


def return_instance(which="node", start=None, end=None, st_num=0):
    """
    Retrieves a specific instance identifier from Prometheus.
    
    Args:
        which: Type of instance ("node" or "libvirt")
        start: Start time in ISO format (defaults to current time - 1 hour)
        end: End time in ISO format (defaults to current time)
        st_num: Index of the instance to retrieve (default 0)
    
    Returns:
        Quoted instance identifier string or -1 on error
    """
    # Set default time range if not provided
    start = start or give_default_dates()[0]
    end = end or give_default_dates()[1]
    
    # Handle node instance type
    if which == "node":
        # Construct URL for node metrics
        url = (
            f"http://localhost:9090/api/v1/query?"
            f"query=node_load1&start={start}&end={end}&step=30s"
        )
        # Get and parse response
        data = rq.get(url).json()
        # Extract and return instance identifier
        return f'"{data["data"]["result"][st_num]["metric"]["instance"]}"'
    
    # Handle libvirt instance type
    elif which == "libvirt":
        # Construct URL for libvirt metrics
        url = (
            f"http://localhost:9090/api/v1/query_range?"
            f"query=libvirt_domain_info_vstate&start={start}&end={end}&step=30s"
        )
        # Get and parse response
        data = rq.get(url).json()
        # Extract and return instance identifier
        return f'"{data["data"]["result"][st_num]["metric"]["instance"]}"'
    
    # Invalid instance type
    return -1


def give_len(start=None, end=None):
    """
    Gets counts of node and libvirt instances available in Prometheus.
    
    Note: Libvirt count is currently disabled in implementation.
    
    Args:
        start: Start time in ISO format (defaults to current time - 1 hour)
        end: End time in ISO format (defaults to current time)
    
    Returns:
        Tuple of (node_count, libvirt_count)
    """
    # Set default time range if not provided
    start = start or give_default_dates()[0]
    end = end or give_default_dates()[1]
    
    try:
        # Node instance count
        node_url = (
            f"http://localhost:9090/api/v1/query?"
            f"query=node_load1&start={start}&end={end}&step=30s"
        )
        node_data = rq.get(node_url).json()
        len_node = len(node_data["data"]["result"])
        
        # Libvirt count - currently disabled
        len_libv = 0
        # Implementation would be similar to node count but using libvirt query
        
        return len_node, len_libv
    except Exception:
        # Return zeros on any error
        return 0, 0


# ======================
# DATA PROCESSING UTILITIES
# ======================

def fill_up_buffer_err(arr, size):
    """
    Pads a numpy array with zeros to reach specified size.
    
    Args:
        arr: Input numpy array
        size: Target size for the array
    
    Returns:
        Padded array if original size < target size, otherwise original array
    """
    # Return original array if already at or above target size
    if len(arr) >= size:
        return arr
    
    # Calculate padding needed
    padding_needed = size - len(arr)
    # Create zero padding
    padding = np.zeros(padding_needed)
    # Concatenate original array with padding
    return np.concatenate((arr, padding))