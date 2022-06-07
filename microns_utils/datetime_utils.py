from datetime import datetime
import pytz

def timezone_converter(timestamp, source_tz, destination_tz, fmt=None):
    """
    Converts timestamp from a source timezone to a destination timezone. 
    To see commonly used timezone options run: 
    
    ```from pytz import common_timezones```
    
    :param timestamp: (datetime.datetime) timestamp to convert
    :param source_tz: (pytz.timezone) source timezone to convert 
    :param destination_tz: (pytz.timezone) destination timezone
    :param fmt: (str) optional - timestamp format to pass to strftime
    
    :returns: (datetime.datetime) converted timestamp
    """
    dest_obj = pytz.timezone(destination_tz)
    source_obj = pytz.timezone(source_tz).localize(timestamp.replace(tzinfo=None))
    converted = dest_obj.normalize(source_obj.astimezone(dest_obj))
    return converted if fmt is None else converted.strftime(fmt)


def current_timestamp(tz='UTC', fmt=None):
    """
    Returns current timestamp in desired timezone (per pytz nomenclature)

    ```from pytz import common_timezones```

    :param tz: (pytz.timezone) desired timezone
    :param fmt: (str) optional - timestamp format to pass to strftime
    :returns: (datetime.datetime) timestamp
    """
    return timezone_converter(datetime.utcnow(), 'UTC', tz, fmt=fmt)

