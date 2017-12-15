from luhyaapi.educloudLog import *
from luhyaapi.hostTools import *
from luhyaapi.rabbitmqWrapper import *
from luhyaapi.vboxWrapper import *
from luhyaapi.settings import *
import time, psutil, requests, os

logger = getncdaemonlogger()

class nc_statusPublisher():
    def __init__(self, ):
        logger.error("nc_status_publisher start running")
        self._ccip = getccipbyconf(mydebug=DAEMON_DEBUG)
        self._old_running_vms = []
        self._new_running_vms = []
        logger.error("cc ip = %s" % self._ccip)

    def job5minuts(self):
        os.system("chown luhya:luhya  /var/log/educloud/*")
        try:
            node_status = self.collect_node_status()
            self.send_node_status_to_cc(node_status)
            time.sleep(5*60)
        except Exception as e:
            logger.error('nc_statusPublisherThread exception = %s' % str(e))

    # find those vms in self._old_running_vms but not in self._new_running_vms
    def find_terminated_vms(self):
        result = []
        for oldvm in self._old_running_vms:
            if oldvm not in self._new_running_vms:
                result.append(oldvm)
        return result

    def job30seconds(self):
        logger.error("start job30seconds")
        
        avail_vm_lsit = getVMlist()
        for avm in avail_vm_lsit:
            if avm['state'] == 'Running':
                self._new_running_vms.append(avm['insid'])
        terminated_vms = self.find_terminated_vms()
        logger.error("old running vms = %s" % json.dumps(self._old_running_vms))
        logger.error("new running vms = %s" % json.dumps(self._new_running_vms))
        logger.error("terminated  vms = %s" % json.dumps(terminated_vms))
        for tvm in terminated_vms:
            message = {}
            message['type']             = "cmd"
            message['op']               = 'ndp/stop'
            message['tid']              = tvm
            message['runtime_option']   = ""

            _message = json.dumps(message)
            zmq_send("127.0.0.1", _message, NC_CMD_QUEUE_PORT)
            logger.error("RDP: find %s is terminated already" % tvm)

        self._old_running_vms = self._new_running_vms
        self._new_running_vms = []

    # every 5 minutes：
    #  - /var/log/educloud/*.log  chown luhya:luhya
    #  - send node status to cc
    # every 30 seconds(if RDP)：
    #  - collect current running vms
    #  - compare to previous ones
    #  - send ndp stop message to cc to clc
    def run(self):
        index = 0
        while True:
            time.sleep(30)
            index += 1
            if not isNDPed():
                self.job30seconds()
            if index == 9:
                index = 0
                self.job5minuts()

    def collect_node_status(self):
        payload = { }
        payload['type']             = 'nodestatus'
        try:
            payload['service_data']     = getServiceStatus('nc')
        except Exception as e:
            logger.error('getServiceStatus exception = %s' % str(e))
        try:
            payload['hardware_data']    = getHostHardware()
            logger.error("nc_statusPublisher-hardware data %s" % json.dumps(payload['hardware_data']))
        except Exception as e:
            logger.error('getHostHardware exception = %s' % str(e))
        try:
            payload['net_data']         = getHostNetInfo()
        except Exception as e:
            logger.error('getHostNetInfo exception = %s' % str(e))
        try:
            payload['vm_data']          = getVMlist()
        except Exception as e:
            logger.error('getVMlist exception = %s' % str(e))

        payload['nid']              = "nc#" + payload['net_data']['mac0'] + "#status"
        return payload

    def send_node_status_to_cc(self, node_status):
        simple_send(logger, self._ccip, 'cc_status_queue', json.dumps(node_status))

def getRuntimeOpiton():
    return ''

def registerMyselfasNC():
    ccip = getccipbyconf(mydebug=DAEMON_DEBUG)
    ccname = getccnamebyconf()

    hostname, hostcpus, hostmem, hostdisk = getHostAttr()
    netlist = getHostNetInfo()

    if isLNC():
        if DAEMON_DEBUG == True:
            url = 'http://%s:8000/cc/api/1.0/register/lnc' % ccip
        else:
            url = 'http://%s/cc/api/1.0/register/lnc' % ccip
        payload = {
            'ip': netlist['ip0'],
            'mac': netlist['mac0'],

            'name': hostname,
            'ccname': ccname,
            'location': '',
            'hypervisor': getHypervisor(),

            'cores': hostcpus,
            'memory': hostmem,
            'disk': hostdisk,
            'runtime_option': getRuntimeOpiton()
        }
    else:
        if DAEMON_DEBUG == True:
            url = 'http://%s:8000/cc/api/1.0/register/server' % ccip
        else:
            url = 'http://%s/cc/api/1.0/register/server' % ccip
        payload = {
            'role': 'nc',
            'name': hostname,
            'cores': hostcpus,
            'memory': hostmem,
            'disk': hostdisk,
            'exip': netlist['exip'],
            'ip0': netlist['ip0'],
            'ip1': netlist['ip1'],
            'ip2': netlist['ip2'],
            'ip3': netlist['ip3'],
            'mac0': netlist['mac0'],
            'mac1': netlist['mac1'],
            'mac2': netlist['mac2'],
            'mac3': netlist['mac3'],
            'hypervisor': getHypervisor(),
            'ccname': ccname,
        }

    r = requests.post(url, data=payload)
    msg = json.loads(r.content)
    if msg['Result'] == "OK":
        logger.error("register NC %s succeed !" % netlist['ip0'])
    else:
        logger.error("register NC %s failed !" % netlist['ip0'])

def main():
    # read /storage/config/cc.conf to register itself to cc
    registerMyselfasNC()

    publisher = nc_statusPublisher()
    publisher.run()


if __name__ == '__main__':
    main()
