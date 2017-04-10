import requests, json, os,sys
from uuid import getnode as get_mac
import wmi

def getLocalMAC():
    mac = get_mac()
    return ''.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

def getMacAddressbyIndex(index=0):
    wmiService = wmi.WMI()
    colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    if len(colNicConfigs) < 1:
        return "" # no active network adaptor

    objNicConfig = colNicConfigs[index]
    mac = objNicConfig.macaddress.replace(":", "")
    return mac

fileflag = '%s\\%s' % (os.environ['TMP'], 'done.txt')
if not os.path.exists(fileflag):
    ip = sys.argv[1]
    clc_ip = "%s" % ip
    # send request to clc
    clc_request_url = "http://%s/clc/api/1.0/vm/afterboot" % clc_ip

    macaddr = getLocalMAC()
    payload = {
        'mac' : getMacAddressbyIndex(0)
    }

    r = requests.post(clc_request_url, data=payload)
    res = json.loads(r.content)
    if res["Result"] == "OK":
        with open(fileflag, 'w') as myfile:
            myfile.write("already done!")

        filepath = '%s\\%s' % (os.environ['TMP'], res['filename'])
        with open(filepath, 'w') as myfile:
            myfile.writelines(res['content'])

        sys.path.append(os.environ['TMP'])
        mn = res['filename'].split('.')[0]
        hc = __import__(mn)
        hc.changeHost()






