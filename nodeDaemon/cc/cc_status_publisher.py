from luhyaapi.educloudLog import *
from luhyaapi.hostTools import *
from luhyaapi.rabbitmqWrapper import *
from luhyaapi.settings import *

import time, psutil, pexpect

logger = getccdaemonlogger()

def runsshfswithexpect():
    clcip = getclcipbyconf()
    password = "luhya"
    base_cmd = 'sshfs -o cache=yes,reconnect %s:/storage/space /storage/space'

    if not os.path.ismount('/storage/space'):
        logger.error("/storage/space is NOT mounted.")
        os.system("fusermount -u /storage/space")
        cmd = base_cmd % (clcip)
        logger.error("run cmd=%s" % cmd)
        child = pexpect.spawn(cmd)
        i = child.expect(['password:', r"yes/no",pexpect.EOF])
        if i == 0:
            child.sendline(password)
        elif i == 1:
            child.sendline("yes")
            ret1 = child.expect(["password:",pexpect.EOF])
            if ret1 == 0:
                child.sendline(password)
        data = child.read()
        logger.error("result is %s" % data)
        child.close()
    else:
        logger.error("/storage/space is mounted.")

def perform_mount():
    logger.error("Enter perform_mount() ... ...")
    # mount clc's /storage/space/{software, pub-data} to local
    if amIwalrus():
        logger.error("I am cc and walrus, no mount any more.")
        return

    runsshfswithexpect()

class cc_statusPublisherThread():
    def __init__(self, ):
        logger.error("cc_status_publisher start running")
        self._clcip = getclcipbyconf(mydebug=DAEMON_DEBUG)
        logger.error("clc ip = %s" % self._clcip)

    def run(self):
        while True:
            perform_mount()

            cc_status = self.collect_cc_status()
            self.send_node_status_to_clc(cc_status)
            time.sleep(5*60)

    def collect_cc_status(self):
        payload = { }
        payload['type']             = 'ccstatus'
        payload['service_data']     = getServiceStatus('cc')
        payload['hardware_data']    = getHostHardware()
        payload['net_data']         = getHostNetInfo()

        payload['ccid']              = "cc#" + payload['net_data']['mac0'] + "#status"

        return payload

    def send_node_status_to_clc(self, node_status):
        simple_send(logger, self._clcip, 'clc_status_queue', json.dumps(node_status))

def main():
    perform_mount()

    publisher = cc_statusPublisherThread()
    publisher.run()

if __name__ == '__main__':
    main()
