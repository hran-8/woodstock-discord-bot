import time
from datetime import datetime
import time

def get_accurate_utc_timestamp():
    """
    Returns the current UTC timestamp (seconds since epoch)
    using the local system clock.
    """
    return time.time()


def get_time_offset():
    api_time = datetime.utcnow().timestamp() 
    local_time = time.time()                  
    return api_time - local_time

TIME_OFFSET = get_time_offset()

def get_corrected_time():
    return time.time() + TIME_OFFSET
