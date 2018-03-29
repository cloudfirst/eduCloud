#! /usr/bin/python

import os, commands, sys, getopt
import time, random
import multiprocessing
from client_sdk import *
from vmslog import *

#################################################################################
# This script will simulate multiple user to initiate the VM instance
# at random time interval and repeate the operation of Start/Stop randomly.
# the only key parameter is the number of account.

# by this way, we can mimic the real world condition to verify the robustness of
# the system, and collect the data of vm booting time.

#################################################################################
# before run this script, make sure
# - create enough number of account by using batch account creation feature.
# usage :
#       startvms -h serverIP  -a account_prefix -p password -n number_of_account

# for example,
#       startvms -h 192.168.0.199 -a auto -n 9 -p auto
# means that there are 9 existing account named from auto1 to auto9, and same passwrod
# "auto" for all of these accounts.

logger = getautologger()

def getlogdatetime():
    return time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")

def ndp_connect(ip, port):
    cmd = '/usr/bin/ndpclient -h ' + ip + ' -p ' + str(port)
    commands.getoutput(cmd)

class autoWorkerProcess(multiprocessing.Process):
    def __init__(self, vmWorker):
        multiprocessing.Process.__init__(self)

        self.vmw = vmWorker
        self.vmobj = None

    def stopWork(self):
        logger.error( "%s process exit." % self.vmobj['tid'] )
        quit()

    def RandomSleep(self, start, end):
        seconds = random.randint(start, end)
        logger.error("Now will sleep %d seconds" % seconds)
        time.sleep(seconds)

    def getCurrentVM(self):
        ret = None
        list_vms = self.vmw.getVDList()
        if len(list_vms['data']) <= 0:
            logger.error( "no vm available for %s, now quit." % self.vmw.user_id )
            self.stopWork()
        else:
            self.vmobj = list_vms['data'][0]

    def delete_vm(self):
        if len(self.vmobj['tid']) > 0 :
            if self.vmobj['state'] == "Running" or self.vmobj['state'] == "running":
                logger.error( "%s clean existing VM" % (self.vmw.user_id))
                self.vmw.delet_vm(self.vmobj)
                self.getCurrentVM()

    def start_vm(self):
        ret = self.vmw.startVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            logger.error( "%s StartVM failed %s" % (self.vmw.user_id, ret['error']))
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()
        else:
            self.vmobj['tid'] = ret['tid']

    def prepare_vm(self):
        ret = self.vmw.prepareVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            logger.error( "%s PrepareVM failed %s" % (self.vmw.user_id, ret['error']))
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def get_prepare_progress(self):
        flag = False
        retry = 100
        while (not flag and retry > 0):
            time.sleep(3)
            ret = self.vmw.getPrepareProgress(self.vmobj)
            if ret['phase'] == 'preparing' and ret['state'] == 'done':
                flag = True
            if ret['state'] == 'stopped':
                break
            retry -= 1

        if not flag or retry <= 0:
            logger.error( "%s PrepareVM too long, restart it" % (self.vmw.user_id))
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def run_vm(self):
        logger.error( "%s RunVM Start" % (self.vmw.user_id))
        ret = self.vmw.runVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            logger.error("%s RunVM failed : %s" % (self.vmw.user_id, ret['error']))
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def get_run_progress(self):
        flag = False
        timer_expired = False
        times = 100
        while (not flag and not timer_expired and times >= 0):
            time.sleep(3)
            ret = self.vmw.getVMStatus(self.vmobj)
            if ret['state'] == 'Running' or ret['state'] == 'running':
                flag = True
            elif ret['state'] == 'stopped':
                timer_expired = True
            times -= 1

        if timer_expired or times <= 0:
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def run(self):
        self.getCurrentVM()
        self.delete_vm()
        self.start_vm()
        self.prepare_vm()
        self.get_prepare_progress()
        self.run_vm()
        self.get_run_progress()

def usage():
    print ""
    print "startvms -h serverIP  -u account_prefix -n number_of_account -p password"
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
    # build vmWorker
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
    # for all valid account, asisgen a proces to
    list_of_process = []
    for vw in list_of_vmWorkers:
        if vw.logon():
            worker = autoWorkerProcess(vw)
            worker.start()
            list_of_process.append(worker)
            # time.sleep(1)

    for w in list_of_process:
        w.join()

if __name__ == '__main__':
    main(sys.argv[1:])
