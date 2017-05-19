import requests, json, os,sys

def usage():
    print "Usage : setDjangoDebug [set | get] [yes | no]"

def main(argv):
    action = argv[0]
    clc_ip = "127.0.0.1"

    if action == "set":
        value = argv[1]
        clc_request_url = "http://%s/clc/api/1.0/set_django_debug" % clc_ip
        payload = {
            'value': value
        }
        r = requests.post(clc_request_url, data=payload)
        res = json.loads(r.content)
        if res["Result"] == "OK":
            print res['msg']
        else:
            print "setDjangoDebug with unknown result"

    if action == "get":
        clc_request_url = "http://%s/clc/api/1.0/get_django_debug" % clc_ip
        r = requests.get(clc_request_url)
        res = json.loads(r.content)
        if res["Result"] == "OK":
            print "Django DEBUG is :" + res['ret']
        else:
            print "setDjangoDebug with unknown result"

if __name__ == "__main__":
   if len(sys.argv) < 3:
       usage()
   else:
       main(sys.argv[1:])