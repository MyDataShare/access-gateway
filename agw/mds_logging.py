from os import getpid
from threading import current_thread
import logging
from typing import Dict, cast
from time import strftime
from collections import defaultdict
from functools import wraps
import time

import bottle

import settings

timed_call_trees: Dict[str, list] = defaultdict(list)


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ll = getLogger(f"agw.{func.__module__}")

        name = func.__name__
        if hasattr(func, '__qualname__'):
            name = func.__qualname__
        else:
            if len(args) > 0:
                name = f"{args[0].__class__.__name__}.{func.__name__}"
        full_name = f"{func.__module__}.{name}"

        myid = f"{getpid()}.{current_thread().native_id}"
        ll.timed(f"START - {name}")
        timed_call_trees[myid].append(full_name)
        start_time = time.time()

        try:
            ret = func(*args, **kwargs)
        except Exception:
            raise
        finally:
            elapsed = time.time() - start_time
            if len(timed_call_trees[myid]) == 0 or timed_call_trees[myid][-1] != full_name:
                ll.warning(f"Timed logging error. Expecting '{full_name}' to close but '{timed_call_trees[myid][-1]}' "
                           "is closing instead.")
            timed_call_trees[myid].pop()
            ll.timed(f"END --- {name} - {elapsed:.5f}s")

        return ret
    return wrapper


class CustomLogFilter(logging.Filter):
    def filter(self, record):
        record.request_id = "unknown"
        if 'request_id' in bottle.request:
            record.request_id = bottle.request['request_id']

        myid = f"{getpid()}.{current_thread().native_id}"
        record.depth = len(timed_call_trees[myid])
        record.indent = ""
        if logging.getLogger().isEnabledFor(MdsLogger.TIMED):
            record.indent = f"{'  ' * record.depth}"

        record.native_id = current_thread().native_id
        return True


class MdsLogger(logging.Logger):
    VERBOSE = 5
    TIMED = 157
    SQL = 17
    REQUEST = 27

    @staticmethod
    def configure_loggers(logger: logging.Logger):
        tz = strftime('%z')
        log_formatter = logging.Formatter(
            f"[%(asctime)s {tz}] [%(process)d.%(native_id)d] [%(request_id)s] [%(levelname)s] (%(depth)d)%(indent)s "
            "[%(name)s] %(message)s")

        logger.propagate = False
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        log_handler.addFilter(CustomLogFilter())
        logger.addHandler(log_handler)

        logging.addLevelName(MdsLogger.VERBOSE, "VERBOSE")
        logging.addLevelName(MdsLogger.TIMED, "TIMED")
        logging.addLevelName(MdsLogger.SQL, "SQL")
        logging.addLevelName(MdsLogger.REQUEST, "REQUEST")

        logger.setLevel(level=settings.LOGGING_LEVEL)

        if settings.LOGGING_COLOR:
            prefix = "\033[38;5;"
            logging.addLevelName(MdsLogger.VERBOSE, f"{prefix}240mVERBO\033[1;0m")
            logging.addLevelName(logging.DEBUG,     f"{prefix}246mDEBUG\033[1;0m")
            logging.addLevelName(MdsLogger.TIMED,   f"{prefix}200mTIMED\033[1;0m")
            logging.addLevelName(MdsLogger.SQL,      f"{prefix}25m_SQL_\033[1;0m")
            logging.addLevelName(logging.INFO,      f"{prefix}231mINFO_\033[1;0m")
            logging.addLevelName(MdsLogger.REQUEST,  f"{prefix}10m_REQ_\033[1;0m")
            logging.addLevelName(logging.WARNING,    f"{prefix}11mWARN_\033[1;0m")
            logging.addLevelName(logging.ERROR,     f"{prefix}160mERROR\033[1;0m")
            logging.addLevelName(logging.CRITICAL,   f"\033[1;101mCRITI\033[1;0m")

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def test_logger(self):
        self.verbose('this is a VERBOSE message')
        self.debug('this is a DEBUG message')
        self.timed('this is a TIMED message')
        self.sql('this is a SQL message')
        self.info('this is an INFO message')
        self.request('this is a REQUEST message')
        self.warning('this is a WARNING message')
        self.error('this is an ERROR message')
        self.critical('this is a CRITICAL message')

    def verbose(self, msg, *args, **kwargs):
        if self.isEnabledFor(MdsLogger.VERBOSE):
            self._log(MdsLogger.VERBOSE, msg, args, **kwargs)

    def timed(self, msg, *args, **kwargs):
        if self.isEnabledFor(MdsLogger.TIMED):
            self._log(MdsLogger.TIMED, msg, args, **kwargs)

    def sql(self, msg, *args, **kwargs):
        if self.isEnabledFor(MdsLogger.SQL):
            self._log(MdsLogger.SQL, msg, args, **kwargs)

    def request(self, msg, *args, **kwargs):
        if self.isEnabledFor(MdsLogger.REQUEST):
            self._log(MdsLogger.REQUEST, msg, args, **kwargs)


logging.setLoggerClass(MdsLogger)


def getLogger(name=None) -> MdsLogger:
    logger = logging.getLogger(name)
    return cast(MdsLogger, logger)
