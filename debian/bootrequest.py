import requests, json, os,sys
from uuid import getnode as get_mac

def getLocalMAC():
    mac = get_mac()
    return ''.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

fileflag = '%s\\%s' % (os.environ['TMP'], 'done.txt')
if not os.path.exists(fileflag):
    ip = sys.argv[1]
    clc_ip = "%s" % ip
    # send request to clc
    clc_request_url = "http://%s/clc/api/1.0/vm/afterboot" % clc_ip

    macaddr = getLocalMAC()
    payload = {
        'mac' : macaddr
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






