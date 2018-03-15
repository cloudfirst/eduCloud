#! /usr/bin/python

import os, commands, sys, getopt
import time, random
from client_sdk import *
from vmslog import *

logger = getautologger()

def usage():
    print ""
    print "stopvms -h serverIP  -u account_prefix -n number_of_account -p password"
    print ""
    print " -h serverIP: the only IP address of educloud web server"
    print " -u account prefix, say, account auto0 has prefix auto"
    print " -n number of account, say, 9 means auto1 to auto9"
    print " -p password, all accounts here share same password"
    print ""

def main(argv):
    if len(argv) == 0:
        usage()
        return

    message = {}
    message['anum']  = -1
    try:
      opts, args = getopt.getopt(argv,"h:u:p:r:n:")
      for opt, arg in opts:
          if opt in ( "-h"):
             message['ip'] =  arg
          if opt in ("-u"):
             message['aprefix'] = arg
          if opt in ("-n"):
             message['anum'] = arg
          if opt in ("-p"):
              message['apw'] = arg
    except getopt.GetoptError:
        usage()
        return

    ##################################################
    list_of_vmWorkers = []
    user_pw = message['apw']
    clc_ip  = message['ip']
    if message['anum']  ==  -1:
        user_id = message['aprefix']
        vmw = cloudDesktopWrapper()
        vmw.setHost(clc_ip, 80)
        vmw.setUser(user_id, user_pw)
        list_of_vmWorkers.append(vmw)
    else:
        for i in range(1, int(message['anum']) + 1):
            user_id = message['aprefix'] + str(i)
            vmw = cloudDesktopWrapper()
            vmw.setHost(clc_ip, 80)
            vmw.setUser(user_id, user_pw)
            list_of_vmWorkers.append(vmw)

    ###################################################
    for w in list_of_vmWorkers:
        time.sleep(1)
        if w.logon():
            time.sleep(1)
            list_vms = w.getVDList()
            if len(list_vms['data']) > 0:
                vmobj = list_vms['data'][0]
                if len(vmobj['tid']) > 1:
                    logger.error( "%s delete running vm %s" % (w.user_id, vmobj['tid']))
                    w.delet_vm(vmobj)
                else:
                    logger.error( "%s dose not have running vm" % (w.user_id))
            else:
                logger.error( "%s dose not have vm" % (w.user_id))


if __name__ == '__main__':
    main(sys.argv[1:])
