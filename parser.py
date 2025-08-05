import dateparser
from datetime import datetime 

def parse_datetime(text): 
    return dateparser.parse(text, settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True})

from datetime import datetime, timezone

def get_now_timestamp():
    return datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
