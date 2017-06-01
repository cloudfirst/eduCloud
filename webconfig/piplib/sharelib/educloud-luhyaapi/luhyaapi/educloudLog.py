import logging
import logging.handlers

MAX_LOGFILE_BYTE = 10 * 1024 * 1024
MAX_LOG_COUNT = 10

def set_log_level(level, loggername='luhya'):
    logger = logging.getLogger(loggername)
    if level == 'error':
        logger.setLevel(logging.ERROR)
    elif level == 'warning':
        logger.setLevel(logging.WARNING)
    elif level == 'info':
        logger.setLevel(logging.INFO)


def init_log(logfile, loggername='luhya'):
    logger = logging.getLogger(loggername)
    ch = logging.handlers.RotatingFileHandler(logfile, maxBytes=MAX_LOGFILE_BYTE, backupCount=MAX_LOG_COUNT)
    formatter = logging.Formatter('<%(asctime)s> <%(levelname)s> <%(module)s:%(lineno)d>\t%(message)s', datefmt='%F %T')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.ERROR)
    return logger

WEB_LOG_FILE        = '/var/log/educloud/educloud.log'
NODE_CLC_LOG_FILE   = '/var/log/educloud/nodedaemon-clc.log'
NODE_CC_LOG_FILE    = '/var/log/educloud/nodedaemon-cc.log'
NODE_NC_LOG_FILE    = '/var/log/educloud/nodedaemon-nc.log'
API_LOG_FILE        = '/var/log/educloud/luhyaapi.log'
SSHFS_LOG_FILE     = '/var/log/educloud/sshfs.log'

def getsshfslogger():
    status_logger = init_log(SSHFS_LOG_FILE)
    return status_logger

def getclcdaemonlogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getwalrusdaemonlogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getccdaemonlogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getncdaemonlogger():
    nc_debug_logger = init_log(NODE_NC_LOG_FILE, 'node')
    return nc_debug_logger

def getclclogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getwalruslogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getcclogger():
    luhya_debug_logger = init_log(WEB_LOG_FILE)
    return luhya_debug_logger

def getluhyaapilogger():
    return init_log(WEB_LOG_FILE)
