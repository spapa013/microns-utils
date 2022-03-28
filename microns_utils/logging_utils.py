import logging
from pathlib import Path
from .misc_utils import classproperty

def configure_logger(filename=None, level='WARNING', format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', datefmt="%m-%d-%Y %I:%M:%S %p %Z", force=True):
    if filename is not None:
        filename = Path(filename)

    log_levels = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'CRITICAL': logging.CRITICAL,
        'DEBUG': logging.DEBUG,
        'ERROR': logging.ERROR,
        None:  logging.NOTSET
    }

    return logging.basicConfig(filename=filename, level=log_levels[level], format=format, datefmt=datefmt, force=force)


class Logger:
    @classproperty
    def log_file_dir(cls):
        return Path(f'/mnt/dj-stor01/microns/logs/')
    
    @classproperty
    def log_file_stem(cls):
        return Path(f'{cls.database}.{cls.__qualname__}.log')

    @classproperty
    def log_file(cls):
        return Path.joinpath(cls.log_file_dir, cls.log_file_stem)

    @classproperty
    def log_level(cls):
        return 'INFO'

    @classmethod
    def configure_logger(cls, filename=None, level=None):
        return configure_logger(
            filename=getattr(cls, 'log_file', None) if filename is None else filename, 
            level=getattr(cls, 'log_level', None) if level is None else level
        )
    
