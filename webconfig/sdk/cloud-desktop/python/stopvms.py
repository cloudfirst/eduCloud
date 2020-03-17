#! /usr/bin/python

import os, commands, sys, getopt
import time, random
from client_sdk import *
from vmslog import *

logger = getautologger()

def usage():
    print ""
    print "stopvms -h serverIP  -u account_prefix -p password [-s 0] -n number_of_account"
    print ""
    print " -h serverIP: the only IP address of educloud web server"
    print " -u account prefix, say, account auto0 has prefix auto"
    print " -p password, all accounts here share same password"
    print " -s start account, default is 0 if not set"
    print " -n number of accounts from start, say, 9 means auto0 to auto8"
    print ""

def main(argv):
    if len(argv) == 0:
        usage()
        return

    message = {}
    message['anum']  = -1
    message['snum']  = 0
    try:
      opts, args = getopt.getopt(argv,"h:u:p:r:n:s:")
      for opt, arg in opts:
          if opt in ( "-h"):
             message['ip'] =  arg
          if opt in ("-u"):
             message['aprefix'] = arg
          if opt in ("-n"):
             message['anum'] = arg
          if opt in ("-p"):
              message['apw'] = arg
          if opt in ("-s"):
              message['snum'] = arg
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
	start = int(message['snum'])
	end   = start + int(message['anum'])
        for i in range(start, end):
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
		    insid = vmobj['tid'].split(':')[2]
		    if insid.find('PVD') == 0:
			logger.error( "%s stop running vm %s" % (w.user_id, vmobj['tid']))	
			w.stopVM(vmobj)
		    else:
                        logger.error( "%s delete running vm %s" % (w.user_id, vmobj['tid']))
                        w.delet_vm(vmobj)
                else:
                    logger.error( "%s dose not have running vm" % (w.user_id))
            else:
                logger.error( "%s dose not have vm" % (w.user_id))


if __name__ == '__main__':
    main(sys.argv[1:])
