#!/usr/bin/python

import os, commands, sys, getopt
import time, random
import multiprocessing
from client_sdk import *

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
#       AutoTest -h serverIP  -a account_prefix -n number_of_account -p password

# for example,
#       AutoTest -h 192.168.0.199 -a auto -n 9 -p auto
# means that there are 9 existing account named from auto0 to auto8, and same passwrod
# "auto" for all of these accounts.


def getlogdatetime():
    return time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")

def ndp_connect(ip, port):
    cmd = '/usr/bin/ndpclient -h ' + ip + ' -p ' + str(port)
    #commands.getoutput(cmd)

class autoWorkerProcess(multiprocessing.Process):
    def __init__(self, vmWorker, retry_times):
        multiprocessing.Process.__init__(self)

        self.retry_times = retry_times
        self.vmw = vmWorker
        self.vmobj = None

    def stopWork(self):
        print "%s process exit." % self.vmobj['tid']
        quit()

    def RandomSleep(self, start, end):
        seconds = random.randint(start, end)
        print "Now will sleep %d seconds" % seconds
        time.sleep(seconds)

    def getCurrentVM(self):
        ret = None
        list_vms = self.vmw.getVDList()
        if len(list_vms['data']) <= 0:
            print "no vm available for %s, now quit." % self.vmw.user_id
            self.stopWork()
        else:
            self.vmobj = list_vms['data'][0]

    def delete_vm(self):
        if len(self.vmobj['tid']) > 0 :
            if self.vmobj['state'] == "Running" or self.vmobj['state'] == "running":
                print "%s %s clean existing VM" % (getlogdatetime(), self.vmw.user_id)
                self.vmw.delet_vm(self.vmobj)
                self.getCurrentVM()

    def start_vm(self):
        ret = self.vmw.startVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            print "%s %s StartVM failed %s" % (getlogdatetime(), self.vmw.user_id, ret['error'])
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()
        else:
            self.vmobj['tid'] = ret['tid']

    def prepare_vm(self):
        ret = self.vmw.prepareVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            print "%s %s PrepareVM failed %s" % (getlogdatetime(), self.vmw.user_id, ret['error'])
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
            print "%s %s PrepareVM too long, restart it" % (getlogdatetime(), self.vmw.user_id)
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def run_vm(self):
        print "%s %s RunVM Start" % (getlogdatetime(), self.vmw.user_id)
        ret = self.vmw.runVM(self.vmobj)
        if ret['Result'] == 'FAIL':
            print "%s %s RunVM failed : %s" % (getlogdatetime(), self.vmw.user_id, ret['error'])
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def get_run_progress(self):
        flag = False
        timer_expired = False
        times = 100
        while (not flag and not timer_expired and times >= 0):
            time.sleep(3)
            ret = self.vmw.getVMStatus(self.vmobj)
            # print 'VM Status is %s' % ret['state']
            if ret['state'] == 'Running' or ret['state'] == 'running':
                # print 'VM is running, now can display it.'
                flag = True
            elif ret['state'] == 'stopped':
                timer_expired = True
            times -= 1

        #if flag:
            #ret = self.vmw.getRDPUrl(self.vmobj)
            #if ret['Result'] == 'FAIL':
            #    print "%s %s Connect failed : %s" % (getlogdatetime(), self.vmw.user_id, ret['error'])
            #else:
            #    ndp_connect(ret['rdp_ip'], ret['rdp_port'])

        if timer_expired or times <= 0:
            self.vmw.errorHandle(self.vmobj)
            self.stopWork()

    def run(self):
        #for i in range(self.retry_times):
        self.getCurrentVM()
        self.delete_vm()

        # randomly start vm after xx seconds
        #print "%s %s Wait %d-%d secods to begin loop" % (getlogdatetime(), self.vmw.user_id, 1, 10)
        #self.RandomSleep(1, 10)
        self.start_vm()
        self.prepare_vm()
        self.get_prepare_progress()
        self.run_vm()
        self.get_run_progress()

def usage():
    print ""
    print "AutoTest -h serverIP  -u account_prefix -n number_of_account -p password [-r retry_times]"
    print ""
    print " -h serverIP: the only IP address of educloud web server"
    print " -u account prefix, say, account auto0 has prefix auto"
    print " -n number of account, say, 9 means auto0 to auto8"
    print " -p password, all accounts here share same password"
    print " -r each account will start/stop vm retry_times, default is 1"
    print ""

def main(argv):
    if len(argv) == 0:
        usage()
        return

    message = {}
    message['retry'] = 1
    message['anum']  = -1
    try:
      opts, args = getopt.getopt(argv,"h:u:n:p:r:")
      for opt, arg in opts:
          if opt in ( "-h"):
             message['ip'] =  arg
          if opt in ("-u"):
             message['aprefix'] = arg
          if opt in ("-n"):
             message['anum'] = arg
          if opt in ("-p"):
              message['apw'] = arg
          if opt in ("-r"):
              message['retry'] = arg
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
        for i in range(int(message['anum'])):
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
            worker = autoWorkerProcess(vw, int(message['retry']))
            worker.start()
            list_of_process.append(worker)

    for w in list_of_process:
        w.join()

    for w in list_of_vmWorkers:
        vmdata = {
            'tid': w.tid
        }
        w.delet_vm(vmdata)

if __name__ == '__main__':
    main(sys.argv[1:])
