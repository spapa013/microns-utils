"""
Utils for working with filepaths.
"""
import os
from pathlib import Path
import datetime
import logging
import pytz

def find_all_matching_files(name, path):
    """
    Finds all files matching filename within path.

    :param name (str): file name to search
    :param path (str): path to search within
    :returns (list): returns list of matching paths to filenames or empty list if no matches found. 
    """
    result = []
    for root, _, files in os.walk(path):
        if name in files:
            result.append(Path(os.path.join(root, name)))
    return result


def validate_filepath(filepath):
    filepath = Path(filepath)
    assert filepath.exists()
    return filepath


def get_file_modification_time(filepath, timezone, fmt=None):
    """
    Gets modification time of file.
    
    :param filepath: (patlib.Path or str) path to file
    :timezone: (str) desired timezone in pytz format (e.g. 'US/Central')
    :fmt: optional (str) timestamp format to pass to strftime 
    
    :returns: datetime object
    """
    ts = datetime.datetime.fromtimestamp(Path(filepath).stat().st_mtime, tz=datetime.timezone.utc)
    localtz = pytz.timezone(timezone)
    utctime = pytz.timezone('UTC').localize(ts.replace(tzinfo=None))
    timestamp = localtz.normalize(utctime.astimezone(localtz))
    return timestamp if fmt is None else timestamp.strftime(fmt)


def append_timestamp_to_filepath(filepath, timestamp, separator='__', verbose=False, return_filepath=False):
    """
    Appends timestamp to provided filepath.
    
    :param filepath: (patlib.Path or str) filepath to directory or file to modify
    :param timestamp: (str or datetime object) timestamp to append
    :param verbose: (bool) logs renamed filepath
    :param return_filepath: (bool) returns renamed filepath patlib.Path
    """
    filepath = Path(filepath)  
    filepath_rn = filepath.with_name(f'{filepath.stem}{separator}{timestamp}')
    filepath.rename(filepath_rn)
    if verbose:
        logging.info(f'File renamed: {filepath_rn}')
    if return_filepath:
        return filepath_rn