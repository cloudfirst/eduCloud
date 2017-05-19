import requests, json, os,sys
from uuid import getnode as get_mac
import wmi, time

import logging
import logging.handlers

MAX_LOGFILE_BYTE = 10 * 1024 * 1024
MAX_LOG_COUNT = 10
LOG_FILE = '%s\\%s' % (os.environ['TMP'], 'luhyavm.log')
fileflag = '%s\\%s' % (os.environ['TMP'], 'done.txt')

def init_log(logfile, loggername='luhya'):
    logger = logging.getLogger(loggername)
    ch = logging.handlers.RotatingFileHandler(logfile, maxBytes=MAX_LOGFILE_BYTE, backupCount=MAX_LOG_COUNT)
    logger.addHandler(ch)
    logger.setLevel(logging.ERROR)
    return logger

luhya_debug_logger = init_log(LOG_FILE)

def getLocalMAC():
    mac = get_mac()
    return ''.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

def getMacAddressbyIndex():
    macs = []
    wmiService = wmi.WMI()
    colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    for col in colNicConfigs:
        macs.append(col.macaddress.replace(":", ""))
    return macs

def checkCLCAvailable(clcip):
    try:
        ret = requests.get("http://" + clcip)
        if ret.status_code == 200:
            luhya_debug_logger.error('checkCLCAvailable -- clc %s is available' % clcip)
            return True
        else:
            luhya_debug_logger.error('checkCLCAvailable -- clc %s is NOT available yet' % clcip)
            return False
    except Exception as e:
        luhya_debug_logger.error('checkCLCAvailable -- exception as %s ' % str(e))
        return False

if not os.path.exists(fileflag):
    luhya_debug_logger.error('done.txt NOT exist, start request ... ...')
    ip = sys.argv[1]
    luhya_debug_logger.error('11111')
    clc_ip = "%s" % ip
    luhya_debug_logger.error('22222')
    # check clc available
    while True:
        luhya_debug_logger.error('33333')
        if checkCLCAvailable(clc_ip) == True:
            break
        else:
            luhya_debug_logger.error('44444')
            time.sleep(1)

    # send request to clc
    luhya_debug_logger.error('55555')
    clc_request_url = "http://%s/clc/api/1.0/vm/afterboot" % clc_ip
    luhya_debug_logger.error('66666')
    macaddrs = getMacAddressbyIndex()
    for mac in macaddrs:
        payload = {
            'mac' : mac.lower()
        }
        luhya_debug_logger.error('send request to clc with mac=%s' % mac.lower())
        r = requests.post(clc_request_url, data=payload)
        res = json.loads(r.content)
        if res["Result"] == "OK":
            luhya_debug_logger.error('request Result SUCCESS')
            with open(fileflag, 'w') as myfile:
                myfile.write("already done!")
                luhya_debug_logger.error('generate done.txt')

            filepath = '%s\\%s' % (os.environ['TMP'], res['filename'])
            with open(filepath, 'w') as myfile:
                myfile.writelines(res['content'])
                luhya_debug_logger.error('generate %s' % res['filename'])

            sys.path.append(os.environ['TMP'])
            mn = res['filename'].split('.')[0]
            luhya_debug_logger.error('run %s' % res['filename'])
            hc = __import__(mn)
            hc.changeHost(luhya_debug_logger)
            break
        else:
            luhya_debug_logger.error('request Result FAIL')
else:
    luhya_debug_logger.error('done.txt ALREADY exist, skip request.')






