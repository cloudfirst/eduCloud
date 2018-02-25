# coding=UTF-8
from luhyaapi.educloudLog import *
from luhyaapi.clcAPIWrapper import *
from luhyaapi.hostTools import *
from luhyaapi.rsyncWrapper import *
from luhyaapi.rabbitmqWrapper import *
from luhyaapi.settings import *
from luhyaapi.zmqWrapper import *
import multiprocessing
import time, json, os

logger = getccdaemonlogger()

def cc_handle_task_status_update(message):
    clcip = getclcipbyconf(mydebug=DAEMON_DEBUG)
    url = "http://%s/%s/task/status/update" % (clcip, "clc")
    payload = {
        "taskstatus" : json.dumps(message['taskstatus'])
    }
    try:
        r = requests.post(url, data=payload, timeout=None)
        logger.error("cc_handle_task_status_update url=%s with status code=%d and payload=%s" % (url, r.status_code, json.dumps(message['taskstatus'], indent=4)))
    except Exception as e:
        logger.error("cc_handle_task_status_update get exception = %s" % str(e))

cc_zmq_handlers = {
    'task/status/update':       cc_handle_task_status_update
}

class cc_cmdConsumer():
    def __init__(self, port=CC_CMD_QUEUE_PORT):
        logger.error("zmq: cc_cmd_consumer start running")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % port)
        self.ret = {}

    def cmdHandle(self, body):
        logger.error("zmq: get cmd body = %s" % body)
        try:
            message = json.loads(body)
            if message.has_key('op') and message['op'] in  cc_zmq_handlers and cc_zmq_handlers[message['op']] != None:
                p = multiprocessing.Process(target=cc_zmq_handlers[message['op']], args=(message,))
                p.start()
            else:
                logger.error("zmq: nc get unknown cmd : %s", body)
        except Exception as e:
            logger.error("zmq: exception =  %s" % str(e))

    def run(self):
        while True:
            msg = self.socket.recv()
            self.socket.send('OK')
            logger.error("cc_cmd_consumer start cmdHandle")
            self.cmdHandle(msg)
            logger.error("cc_cmd_consumer end cmdHandle")



def main():
    consumer = cc_cmdConsumer()
    consumer.run()


if __name__ == '__main__':
    main()
