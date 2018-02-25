import zmq

from luhyaapi.educloudLog import *
logger = getluhyaapilogger()

CLC_CMD_QUEUE_PORT = 9997
CC_CMD_QUEUE_PORT  = 9998
NC_CMD_QUEUE_PORT  = 9999

def zmq_send(ip, msg, port):
    try:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://%s:%s" % (ip,port))

        socket.send(msg, flags=zmq.NOBLOCK)
        message = socket.recv()
        logger.error("zmq_send result = %s" % message)
    except Exception as e:
        logger.error("zmq_send() with exception:%s" % str(e))

def zmq_recv():
    pass