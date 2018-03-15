from luhyaapi.hostTools import *
from luhyaapi.educloudLog import *
from luhyaapi.rabbitmqWrapper import *
from luhyaapi.rsyncWrapper import *
from luhyaapi.vboxWrapper import *
from luhyaapi.clcAPIWrapper import *
from luhyaapi.zmqWrapper import *
import pika, json, time, shutil, os, commands, zmq
import multiprocessing, pexpect, memcache

logger = getncdaemonlogger()

def getParallNumber():
    pnum = get_desktop_res()['max_pboot_vms']
    if pnum <= 0:
        # not configured
        logger.error("max_pboot_vms not configured, use the value of number of cpu core, minus one." )
        pnum = multiprocessing.cpu_count() - 1
        if pnum <= 1:
            pnum = 1
    logger.error("max_pboot_vms=%d" % pnum)
    return pnum

my_semaphores = multiprocessing.Semaphore(getParallNumber())

my_pboot_delay = get_desktop_res()['max_pboot_delay']
logger.error("max_pboot_delay=%d" % my_pboot_delay)

my_wait_to_kill_interval = get_desktop_res()['max_wait_to_kill_interval']*60
logger.error("max_wait_to_kill_interval=%d seconds" % my_wait_to_kill_interval)

delete_semaphor = multiprocessing.Semaphore(1)

#################################################
#  worker thread
class prepareImageTaskThread(multiprocessing.Process):
    def __init__(self, tid, runtime_option):
        multiprocessing.Process.__init__(self)
        retval                  = tid.split(':')
        self.tid                = tid
        self.srcimgid           = retval[0]
        self.dstimgid           = retval[1]
        self.insid              = retval[2]
        self.runtime_option     = json.loads(runtime_option)
        self.ccip               = getccipbyconf()
        self.download_rpc       = RpcClient(logger, self.ccip)
        logger.error('prepareImageTaskThread inited, tid=%s' % tid)

    def checkCLCandCCFile(self, paras):
        logger.error("Enter checkCLCandCCFile() ... ... ")
        result = verify_clc_cc_image_info(self.ccip, self.tid)
        logger.error("clc vs cc image info = %s" % json.dumps(result))

        if paras == 'luhya':
            if result['clc']['version'] == result['cc']['version'] and \
               result['clc']['size']    == result['cc']['size']:
                return 'NO'
            else:
                return "YES"

        if paras == 'db':
            if result['clc']['dbsize'] == result['cc']['dbsize']:
                return 'NO'
            else:
                return 'YES'

    # RPC call to ask CC download image from walrus
    def downloadFromWalrus2CC(self, data):
        logger.error('downloadFromWalrus2CC start ... ...')
        retvalue = "OK"

        needDownloading = self.checkCLCandCCFile(data['rsync'])
        logger.error("needDownloading = %s" % needDownloading)
        if needDownloading == 'NO':
            response = {
                'type'      : 'taskstatus',
                'phase'     : "preparing",
                'state'     : 'downloading',
                'progress'  : 0,
                'tid'       : self.tid,
                'prompt'    : '',
                'errormsg'  : '',
                'failed'    : 0,
                'done'      : 1,
            }
            self.forwardTaskStatus2CC(json.dumps(response))
            logger.error('image in walrus info is SAME as that in cc.')
        else:
            while True:
                response = self.download_rpc.call(cmd=data['cmd'], tid=data['tid'], paras=data['rsync'])
                logger.error("self.download_rpc.call return = %s" % response)
                response = json.loads(response)

                if response['failed'] == 1:
                    logger.error(' ----- failed . ')
                    retvalue = "FALURE"
                    response['state'] = 'init'
                    self.forwardTaskStatus2CC(json.dumps(response))
                    break
                elif response['done'] == 1:
                    logger.error(' ----- done . ')
                    response['progress'] = 0
                    self.forwardTaskStatus2CC(json.dumps(response))
                    break
                else:
                    logger.error('progress = %s' % response['progress'])
                    self.forwardTaskStatus2CC(json.dumps(response))

                time.sleep(2)

        return retvalue

    def forwardTaskStatus2CC(self, response):
        simple_send(logger, self.ccip, 'cc_status_queue', response)

    def getImageTask(self, imgid, ttype):
        worker = None
        mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        key = str("%s#%s" % (ttype, imgid))
        try:
            worker = mc.get(key)
        except Exception as e:
            logger.error("getImageTask except = %s" % str(e))

        return worker

    def setImageTask(selfself, imgid, progress, ttype):
        mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        key = str("%s#%s" % (ttype, imgid))
        try:
            mc.set(key, progress, 60*60)
        except Exception as e:
            logger.error("setImageTask except = %s" % str(e))

    def deleteImageTask(self, imgid, ttype):
        mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        key = str("%s#%s" % (ttype, imgid))
        try:
            mc.delete(key, 0)
        except Exception as e:
            logger.error("setImageTask except = %s" % str(e))


    def downloadFromCC2NC(self, data):
        logger.error('Enter downloadFromCC2NC  ... ...')
        locale_string = getlocalestring()
        retvalue = "OK"

        payload = {
            'type'      : 'taskstatus',
            'phase'     : "preparing",
            'state'     : "downloading",
            'progress'  : 0,
            'tid'       : self.tid,
            'prompt'    : '',
            'errormsg'  : "",
            'failed'    : 0,
            'done'      : 0,
        }

        paras = data['rsync']

        self.cc_img_info        = getImageVersionFromCC(self.ccip, self.tid)
        self.nc_img_version, self.nc_img_size = getLocalImageInfo(self.srcimgid)
        self.nc_dbsize          = getLocalDatabaseInfo(self.srcimgid, self.insid)

        if paras == 'luhya':
            prompt      = locale_string['prmptDfromCC2NC_image']
            source      = "rsync://%s/%s/%s" % (self.ccip, data['rsync'], self.srcimgid)
            destination = "/storage/images/"

            if self.cc_img_info['data']['version'] == self.nc_img_version and \
               self.cc_img_info['data']['size'] == self.nc_img_size and \
               self.nc_img_size > 0:
                payload['progress'] = 0
                payload['done']     = 1
                self.forwardTaskStatus2CC(json.dumps(payload))
                logger.error("image in cc is SAME as that in nc. ")
                return retvalue
            else:
                payload['prompt'] = prompt
                imgid = self.srcimgid
                rsync_result = self.getImageTask(imgid, paras)
                if rsync_result  == None:
                    worker = rsyncWorkerThread(logger, source, destination)
                    worker.start()
                    self.setImageTask(imgid, {"progress": 0}, paras)
                    logger.error("tid=%s start the image downloading worker %s" % (self.tid, worker))
                else:
                    logger.error("tid=%s share the image downloading worker" % (self.tid))


        if paras == 'db':
            prompt      = locale_string['prmptDfromCC2NC_db']
            source      = "rsync://%s/%s/%s" % (self.ccip, data['rsync'], self.srcimgid)
            destination = "/storage/space/database/images/"

            if self.cc_img_info['data']['dbsize'] == self.nc_dbsize and \
               self.nc_dbsize > 0:
                payload['progress'] = 0
                payload['done']     = 1
                self.forwardTaskStatus2CC(json.dumps(payload))
                logger.error("database in cc is SAME as that in nc. ")
                return retvalue
            else:
                payload['prompt'] = prompt
                imgid = self.srcimgid
                rsync_result = self.getImageTask(imgid, paras)
                if rsync_result  == None:
                    worker = rsyncWorkerThread(logger, source, destination)
                    worker.start()
                    self.setImageTask(imgid, {"progress": 0}, paras)
                    logger.error("tid=%s start the data downloading worker %s" % (self.tid, worker))
                else:
                    logger.error("tid=%s share the data downloading worker %s" % (self.tid))

        if rsync_result == None:
            while True:
                time.sleep(2)
                payload['progress'] = worker.getprogress()
                payload['failed'] = worker.isFailed()
                payload['done'] = worker.isDone()
                if worker.isFailed():
                    logger.error(' ----- failed . ')
                    payload['failed'] = worker.isFailed()
                    payload['errormsg'] = worker.getErrorMsg()
                    payload['state'] = 'init'
                    self.forwardTaskStatus2CC(json.dumps(payload))
                    self.setImageTask(imgid, json.dumps(payload), paras)
                    retvalue = "FALURE"
                    break
                elif worker.isDone():
                    logger.error(' ----- Done . ')
                    payload['progress'] = 0
                    payload['done'] = 1
                    self.forwardTaskStatus2CC(json.dumps(payload))
                    self.setImageTask(imgid, json.dumps(payload), paras)
                    break
                else:
                    logger.error('%s:progress = %s' % (self.tid, payload['progress']))
                    self.forwardTaskStatus2CC(json.dumps(payload))
                    self.setImageTask(imgid, json.dumps(payload), paras)
        else:
            while True:
                time.sleep(2)
                payload = self.getImageTask(imgid, paras)
                payload = json.loads(payload)
                payload['tid'] = self.tid
                logger.error('%s:progress = %s' % (self.tid, payload['progress']))
                self.forwardTaskStatus2CC(json.dumps(payload))
                if payload['failed'] or payload['done']:
                    logger.error("shared download thread is failed or done for tid=%s" % self.tid)
                    break

        return retvalue

    def cloneImage(self, data):
        logger.error('cloneImage start for %s ... ...' % data['rsync'])
        retvalue = "OK"
        locale_string = getlocalestring()

        payload = {
                'type'      : 'taskstatus',
                'phase'     : "preparing",
                'state'     : "cloning",
                'progress'  : 0,
                'tid'       : self.tid,
                'prompt'    : '',
                'errormsg'  : "",
                'failed'    : 0,
                'done'      : 0,
        }

        dstfile  = None
        hdds = get_vm_hdds()
        need_delete = False
        need_clone  = False

        if data['rsync'] == 'luhya':
            payload['prompt'] =  locale_string['promptClone_image']
            srcfile  = "/storage/images/%s/machine"      % self.srcimgid
            dstfile  = "/storage/tmp/images/%s/machine"  % self.dstimgid
            if self.srcimgid != self.dstimgid:
                need_clone  = True
                need_delete = True

        if data['rsync'] == 'db':
            payload['prompt'] =  locale_string['promptClone_db']

            if self.insid.find('TMP') == 0:
                if self.runtime_option['usage'] == 'server':
                    srcfile  = "/storage/space/database/images/%s/database" % self.srcimgid
                    dstfile = "/storage/space/database/images/%s/database" % self.dstimgid
                    if self.srcimgid != self.dstimgid:
                        need_delete = True
                        need_clone = True
                    else:
                        need_delete = False
                        need_clone = False
                else:
                    srcfile  = "/storage/images/%s/data" % self.srcimgid
                    dstfile  = "/storage/tmp/images/%s/data" % self.dstimgid
                    if self.srcimgid != self.dstimgid:
                        need_delete = True
                        need_clone = True
                    else:
                        need_delete = False
                        need_clone = False

            if self.insid.find('VD')  == 0 or self.insid.find('TVD') == 0 or self.insid.find('PVD') == 0:
                pass
            if self.insid.find('VS')  == 0:
                dstfile  = "/storage/space/database/instances/%s/database" % self.insid
                if dstfile in hdds or os.path.exists(dstfile):
                    pass
                else:
                    need_clone = True

        if need_delete == True:
            cmd = VBOX_MGR_CMD + " closemedium disk %s --delete" % dstfile
            ret = commands.getoutput(cmd)
            logger.error("cmd line = %s" % cmd)
            logger.error("result = %s" % ret)

        if need_clone == True:
            src_size = os.path.getsize(srcfile)
            cmd = VBOX_MGR_CMD + " clonehd " + " " + srcfile + " " + dstfile
            logger.error("cmd line = %s", cmd)
            procid = pexpect.spawn(cmd)
            logger.error("start to watch clonehd progress ... ... ")

            while procid.isalive():
                try:
                    dst_size = os.path.getsize(dstfile)
                except:
                    dst_size = 0

                ratio = int(dst_size * 100.0 / src_size)
                logger.error('current clone percentage is %d' % ratio)
                payload['progress'] = ratio
                self.forwardTaskStatus2CC(json.dumps(payload))
                time.sleep(2)

            if procid.status == 0:
                payload['progress'] = 100
                payload['done'] = 1
                logger.error('current clone percentage is done')
                self.forwardTaskStatus2CC(json.dumps(payload))
            else:
                logger.error(' ----- failed . ')
                retvalue = "FAILURE"
                payload['failed'] = 1
                payload['state']  = 'init'
                payload['errormsg'] = 'Failed in Cloning file.'
                self.forwardTaskStatus2CC(json.dumps(payload))

        return retvalue


    def run(self):
        payload = {
            'type'      : 'taskstatus',
            'phase'     : "preparing",
            'state'     : 'done',
            'progress'  :  0,
            'tid'       : self.tid,
            'prompt'    : '',
            'errormsg'  : '',
            'failed'    : 0,
        }
        done_1 = False
        done_2 = False

        data = {}
        data['cmd']     = 'image/prepare'
        data['tid']     =  self.tid
        data['rsync']   = 'luhya'
        try:
            if self.downloadFromWalrus2CC(data) == "OK":
                logger.error("%s:downloadFromWalrus2CC = OK for image" % self.tid)
                if self.downloadFromCC2NC(data) == "OK":
                    logger.error("%s:downloadFromCC2NC = OK for image" % self.tid)
                    if self.cloneImage(data) == "OK":
                        logger.error("%s:cloneImage = OK for image" % self.tid)
                        done_1 = True
                        logger.error("%s:done_1 = True" % self.tid)

            if done_1 == True:
                data['rsync'] = 'db'
                if self.runtime_option['usage'] == 'server': # desktop, server, app
                    if self.downloadFromWalrus2CC(data) == "OK":
                        if self.cloneImage(data) == "OK":
                            done_2 = True
                else:# clone D disk for user if needed
                    self.cloneImage(data)
                    done_2 = True
                    logger.error("%s:done_2 = True" % self.tid)

            if done_1 == False or done_2 == False:
                logger.error('%s:send cmd image/prepare/failure' % self.tid)
                payload['failed']   = 1
                if done_1 == False:
                    payload['errormsg'] = "prepare system disk failed. try again."
                if done_2 == False:
                    payload['errormsg'] = "prepare data disk failed. try again"
                payload['state']    = 'init'
                safe_update_task_status(self.ccip, "cc", payload)
            else:
                logger.error('%s:send cmd image/prepare/success' % self.tid)
                safe_update_task_status(self.ccip, "cc", payload)
        except Exception as e:
            logger.error("%s:prepareImageTask Exception: %s" % (self.tid, str(e)))
            logger.error('%s:after exception, send cmd image/prepare/failure' % self.tid)
            payload['failed']   = 1
            payload['errormsg'] = "Get Excetpion:" + str(e)
            payload['state']    = 'init'
            safe_update_task_status(self.ccip, "cc", payload)

class SubmitImageTaskThread(multiprocessing.Process):
    def __init__(self, tid, runtime_option):
        multiprocessing.Process.__init__(self)
        retval = tid.split(':')
        self.tid      = tid
        self.srcimgid = retval[0]
        self.dstimgid = retval[1]
        self.insid    = retval[2]
        self.ccip     = getccipbyconf()
        self.runtime_option = json.loads(runtime_option)
        self.download_rpc = RpcClient(logger, self.ccip)
        if self.dstimgid != self.srcimgid:
            self.vm_root_dir = "/storage/tmp/"
            self.root_dir    = "/storage/tmp/images/"
        else:
            self.vm_root_dir = "/storage/"
            self.root_dir    = "/storage/images/"
        self.vboxmgr = vboxWrapper(self.dstimgid, self.insid, self.vm_root_dir)

    # RPC call to ask CC download image from walrus
    def submitFromCC2Walrus(self, data):
        logger.error('submitFromCC2Walrus start ... ...')
        retvalue = "OK"

        while True:
            response = self.download_rpc.call(cmd=data['cmd'], tid=data['tid'], paras=data['rsync'])
            response = json.loads(response)

            if response['failed'] == 1:
                logger.error(' ----- failed . ')
                response['state'] = 'init'
                retvalue = "FALURE"
                self.forwardTaskStatus2CC(json.dumps(response))
                break
            if response['done'] == 1:
                logger.error(' ----- done . ')
                response['progress'] = 100
                self.forwardTaskStatus2CC(json.dumps(response))
                break
            else:
                logger.error('progress = %s' % response['progress'])
                self.forwardTaskStatus2CC(json.dumps(response))

            time.sleep(2)

        return retvalue

    def forwardTaskStatus2CC(self, response):
        simple_send(logger, self.ccip, 'cc_status_queue', response)

    def submitFromNC2CC(self, data):
        logger.error('submitFromNC2CC start ... ...')
        locale_string = getlocalestring()

        payload = {
            'type'      : 'taskstatus',
            'phase'     : "submitting",
            'state'     : 'uploading',
            'progress'  : 0,
            'tid'       : self.tid,
            'prompt'    : '',
            'errormsg'  : "",
            'failed'    : 0,
            'done'      : 0,
        }

        retvalue = "OK"
        prompt = 'Uploading file from NC to CC ... ...'

        if amIcc() and self.srcimgid == self.dstimgid:
            logger.error(' ----- I am CC and it is modify op, no need to upload any more . ')
            payload['progress'] = 0
            payload['done']     = 1
            payload['prompt']   = prompt
            self.forwardTaskStatus2CC(json.dumps(payload))
            return retvalue

        paras = data['rsync']

        if paras == 'luhya':
            prompt      = locale_string['promptUfromNC2CC_image']
            source      = self.root_dir + self.dstimgid
            destination = "rsync://%s/%s/" % (self.ccip, data['rsync'])
            payload['prompt'] = prompt
        if paras == 'db':
            prompt      = locale_string['promptUfromNC2CC_db']
            payload['prompt'] = prompt
            payload['progress'] = 0
            payload['done']   = 1
            self.forwardTaskStatus2CC(json.dumps(payload))
            return retvalue

        worker = rsyncWorkerThread(logger, source, destination)
        worker.start()

        while True:
            payload['progress'] = worker.getprogress()
            payload['failed'] = worker.isFailed()
            payload['done'] = worker.isDone()
            if worker.isFailed():
                logger.error(' ----- failed . ')
                payload['failed'] = worker.isFailed()
                payload['errormsg'] = worker.getErrorMsg()
                payload['state'] = 'init'
                self.forwardTaskStatus2CC(json.dumps(payload))
                retvalue = "FALURE"
                break
            elif worker.isDone():
                logger.error(' ----- Done . ')
                payload['progress'] = 0
                self.forwardTaskStatus2CC(json.dumps(payload))
                break
            else:
                logger.error('progress = %s' % payload['progress'])
                self.forwardTaskStatus2CC(json.dumps(payload))
            time.sleep(2)

        return retvalue

    def delete_snapshort(self):
        logger.error(' -------- delete_snapshort')

        snapshot_name = "thomas"
        if self.vboxmgr.isSnapshotExist(snapshot_name):
            out = self.vboxmgr.delete_snapshot(snapshot_name)
            logger.error("luhya: delete snapshort with result - out=%s ", out)

    def task_finished(self):
        logger.error(' -------- task_finished')

        find_registered_vm = False
        vminfo = getVMlist()
        for vm in vminfo:
            if vm['insid'] == self.insid:
                find_registered_vm = True
                break

        if self.srcimgid != self.dstimgid:
            if find_registered_vm == True:
                ret = self.vboxmgr.unregisterVM()
                logger.error("--- vboxmgr.unregisterVM ret=%s" % (ret))
                self.vboxmgr.deleteVMConfigFile()

            hdds = get_vm_hdds()
            dstfile = '/storage/tmp/images/%s/machine' % self.dstimgid
            if dstfile in hdds:
                cmd = VBOX_MGR_CMD + " closemedium disk %s --delete" % dstfile
                logger.error("cmd line = %s", cmd)
                commands.getoutput(cmd)

            if os.path.exists(os.path.dirname(dstfile)):
                logger.error('rm %s' % os.path.dirname(dstfile))
                if os.path.exists(os.path.dirname(dstfile)):
                    shutil.rmtree(os.path.dirname(dstfile))

            logger.error("--- task_finish is Done whit src <> dst")
        else:
            if find_registered_vm == True:
                ret = self.vboxmgr.unregisterVM()
                self.vboxmgr.deleteVMConfigFile()
                logger.error("--- vboxmgr.unregisterVM ret=%s" % (ret))

            oldversionNo = ReadImageVersionFile(self.dstimgid)
            newversionNo = IncreaseImageVersion(oldversionNo)
            WriteImageVersionFile(self.dstimgid, newversionNo)
            logger.error("update version to %s" % newversionNo)
            logger.error("--- task_finish is Done whit src == dst")

    def run(self):
        payload = {
            'type'      : 'taskstatus',
            'phase'     : "submitting",
            'state'     : 'done',
            'progress'  :  0,
            'tid'       : self.tid,
            'prompt'    : '',
            'errormsg'  : '',
            'failed'    : 0,
        }

        done_1 = False
        done_2 = False

        data = {}
        data['cmd']     = 'image/submit'
        data['tid']     =  self.tid
        data['rsync']   = 'luhya'
        try:
            self.delete_snapshort()

            if self.submitFromNC2CC(data) == "OK":
                if self.submitFromCC2Walrus(data) == "OK":
                    done_1 = True

            if done_1 == True:
                if self.runtime_option['usage'] == 'server':
                    data['rsync'] = 'db'
                    if self.submitFromCC2Walrus(data) == "OK":
                        done_2 = True
                else:
                    done_2 = True

            if done_1 == False or done_2 == False:
                logger.error('send cmd image/submit/failure ')
                self.download_rpc.call(cmd="image/submit/failure", tid=data['tid'], paras=data['rsync'])
            else:
                self.task_finished()
                payload = json.dumps(payload)
                self.forwardTaskStatus2CC(payload)
                time.sleep(20)
                logger.error('send cmd image/submit/success whith payload=%s' % payload)
                self.download_rpc.call(cmd="image/submit/success", tid=data['tid'], paras=data['rsync'])

        except Exception as e:
            logger.error("submitImageTask Exception Error Message : %s" % str(e))
            logger.error('send cmd image/submit/failure ')
            self.download_rpc.call(cmd="image/submit/failure", tid=self.tid, paras=data['rsync'])

            payload['failed'] = 1
            payload['errormsg'] = str(e)
            payload['state'] = 'init'
            self.forwardTaskStatus2CC(json.dumps(payload))

class runImageTaskThread(multiprocessing.Process):
    def __init__(self, tid, runtime_option):
        multiprocessing.Process.__init__(self)

        self.ccip     = getccipbyconf()

        retval = tid.split(':')
        self.tid      = tid
        self.srcimgid = retval[0]
        self.dstimgid = retval[1]
        self.insid    = retval[2]
        self.runtime_option = json.loads(runtime_option)

        self.rpcClient = RpcClient(logger, self.ccip)

        if self.srcimgid != self.dstimgid:
            self.rootdir = "/storage/tmp"
        else:
            self.rootdir = "/storage"

    def vbox_createVM(self):
        self.vboxmgr = vboxWrapper(self.dstimgid, self.insid, self.rootdir)

        flag = True
        payload = {
            'type'      : 'taskstatus',
            'phase'     : "editing",
            'state'     : 'booting',
            'tid'       : self.tid,
            'errormsg'  : '',
            'failed'    : 0,
        }

        vboxmgr = self.vboxmgr
        bridged_ifs = get_vm_ifs()

        # register VM
        if not vboxmgr.isVMRegistered():
            logger.error("--- --- --- vm %s is not registered" % vboxmgr.getVMName())
            if vboxmgr.isVMRegisteredBefore():
                logger.error("--- --- --- vm %s is registered before" % vboxmgr.getVMName())
                ret = vboxmgr.registerVM()
            else:
                logger.error("--- --- --- vm %s is not registered yet" % vboxmgr.getVMName())
                try:
                    ostype_value = self.runtime_option['ostype']
                    ret = vboxmgr.createVM(ostype=ostype_value)
                    logger.error("--- --- --- vboxmgr.createVM, error=%s" % ret)
                    ret = vboxmgr.registerVM()
                    logger.error("--- --- --- vboxmgr.registerVM, error=%s" % ret)
                    if self.runtime_option['disk_type'] == 'IDE':
                        ret = vboxmgr.addCtrl(" --name IDE --add ide ")
                    else:
                        ret = vboxmgr.addCtrl(" --name SATA --add sata ")
                        ret = vboxmgr.addCtrl(" --name IDE --add ide ")
                        # ret, err = vboxmgr.addCtrl(" --name IDE --add ide ")
                    logger.error("--- --- --- vboxmgr.addCtrl, error=%s" % ret)

                    # add disks
                    for disk in self.runtime_option['disks']:
                        ret = vboxmgr.attachHDD(self.runtime_option['disk_type'], disk['mtype'], disk['file'])
                        logger.error("--- --- --- vboxmgr.attachHDD %s, error=%s" % (disk['file'], ret))
                        time.sleep(2)

                    # add folders
                    for folder in self.runtime_option['folders']:
                        ret = vboxmgr.attachSharedFolder(folder['name'], folder['path'])
                        logger.error("--- --- --- vboxmgr.attachSharedFolder %s=%s, error=%s" % (folder['name'], folder['path'] , ret))
                        time.sleep(2)

                    # in servere side, each VM has 4G mem
                    _cpus    = self.runtime_option['cpus']
                    _memory  = self.runtime_option['memory'] * 1024

                    networkcards = self.runtime_option["networkcards"]
                    _network_para = ""
                    index = 1
                    for netcard in networkcards:
                        if netcard["nic_mode"] == "bridge":
                            _network_para += " --nic%s bridged --bridgeadapter%s %s --nictype%s %s --macaddress%s %s " % (str(index), str(index), bridged_ifs[0], str(index), netcard['nic_type'], str(index), netcard['nic_mac'])
                        if netcard["nic_mode"] == "nat":
                            _network_para += " --nic%s nat --nictype%s %s " % (str(index), str(index), netcard['nic_type'])
                        index += 1

                    if self.runtime_option['protocol'] != 'RDP':
                        ostypepara_value = _network_para + " --audio none "
                    else:
                        ostypepara_value = _network_para +  self.runtime_option['audio_para']
                    ret = vboxmgr.modifyVM(osTypeparam=ostypepara_value, cpus = _cpus, mem=_memory, )
                    logger.error("--- --- --- vboxmgr.modifyVM, error=%s" % ret)

                    # in server side, configure headless property
                    if self.runtime_option['protocol'] == 'RDP':
                        portNum = self.runtime_option['rdp_port']
                        ret = vboxmgr.addHeadlessProperty(port=portNum)
                        logger.error("--- --- --- vboxmgr.addHeadlessProperty, error=%s" % ret)

                        if self.runtime_option['usage'] == 'desktop':
                            ret = vboxmgr.addVRDPproperty()
                            logger.error("--- --- --- vboxmgr.addVRDPproperty for video channel, error=%s" % ret)

                    ret = vboxmgr.unregisterVM()
                    logger.error("--- --- --- vboxmgr.unregisterVM, error=%s" % ret)
                    ret = vboxmgr.registerVM()
                    logger.error("--- --- --- vboxmgr.registerVM, error=%s" % ret)
                except Exception as e:
                    logger.error("createVM Exception error=%s" % str(e))
                    ret = vboxmgr.unregisterVM()
                    vboxmgr.deleteVMConfigFile()
                    flag = False
                    payload['failed']   = 1
                    payload['state']    = 'stopped'
                    payload['errormsg'] = "vbox_createVM exception=" + str(e)

        logger.error('createvm result: %s' % json.dumps(payload, indent=4))
        safe_update_task_status(self.ccip, "cc", payload)
        return flag

    def kvm_createVM(self):
        pass

    # need to consider vd & vs creation
    # c: d: e: f:
    def createvm(self):
        hyper = getHypervisor()
        if hyper == 'vbox':
            return self.vbox_createVM()
        if hyper == 'kvm':
            return self.kvm_createVM()

    def vbox_runVM(self):
        flag = True
        payload = {
            'type'      : 'taskstatus',
            'phase'     : "editing",
            'state'     : 'running',
            'tid'       : self.tid,
            'errormsg'  : '',
            'failed'    : 0,
        }

        vboxmgr = self.vboxmgr

        try:
            if not vboxmgr.isVMRunning():
                logger.error("vbox_runVM: %s is not running" % self.tid)
                # every time before running, take a NEW snapshot
                snapshot_name = "thomas"
                if self.runtime_option['run_with_snapshot'] == 1:
                    if self.insid.find('TMP') == 0:
                        # create snapshot if not exist
                        # do nothing if exist
                        if not vboxmgr.isSnapshotExist(snapshot_name):
                            ret = vboxmgr.take_snapshot(snapshot_name)

                    if self.insid.find('TVD') == 0:
                        # create snapshot if not exist
                        # restore snapshot if exist
                        if not vboxmgr.isSnapshotExist(snapshot_name):
                            ret = vboxmgr.take_snapshot(snapshot_name)
                        else:
                            ret = vboxmgr.restore_snapshot(snapshot_name)

                    if self.insid.find('VD') == 0:
                        # create snapshot if not exist
                        # restore snapshot if exist
                        if not vboxmgr.isSnapshotExist(snapshot_name):
                            ret = vboxmgr.take_snapshot(snapshot_name)
                        else:
                            ret = vboxmgr.restore_snapshot(snapshot_name)

                    if self.insid.find("PVD") == 0:
                        # create snapshot if not exist
                        # do nothing if exist
                        if not vboxmgr.isSnapshotExist(snapshot_name):
                            ret = vboxmgr.take_snapshot(snapshot_name)

                    if self.insid.find('VS') == 0:
                        # create snapshot if not exist
                        # restore snapshot if exist
                        if not vboxmgr.isSnapshotExist(snapshot_name):
                            ret = vboxmgr.take_snapshot(snapshot_name)
                        else:
                            ret = vboxmgr.restore_snapshot(snapshot_name)

                logger.error("vbox_runVM:  check whether it is LNC")
                if isLNC():
                    headless = False
                else:
                    headless = True

                if self.runtime_option['protocol'] == 'NDP':
                    logger.error("vbox_runVM: ndp_runVM %s %s " % (self.runtime_option['rdp_ip'], self.runtime_option['rdp_port']))
                    vboxmgr.ndp_runVM(self.runtime_option['rdp_ip'], self.runtime_option['rdp_port'])
                else:
                    logger.error("vbox_runVM: vbox_runVM")
                    vboxmgr.runVM(headless)
            else:
                logger.error("--- --- --- vboxmgr.SendCAD b")
                vboxmgr.SendCAD()
        except Exception as e:
            logger.error("--- --- --- vboxmgr.runVM exception : %s " % str(e))
            flag = False
            payload['failed'] = 1
            payload['state'] = 'stopped'
            payload['errormsg'] = "vbox_runVM exception=" + str(e)
            process_delete_cmd(self.tid, self.runtime_option)

        logger.error('runvm result: %s' % json.dumps(payload, indent=4))
        safe_update_task_status(self.ccip, "cc", payload)
        return flag

    def kvm_runVM(self):
        pass

    def markInMemcache(self):
        mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        key = "nc_startvm#" + str(self.insid)
        mc.set(key, self.tid, my_wait_to_kill_interval)
        logger.error("save %s=%s into memcache" % (key, self.tid))

    def runvm(self):
        hyper = getHypervisor()
        if hyper == 'vbox':
            return self.vbox_runVM()
        if hyper == 'kvm':
            return self.kvm_runVM()

    def run(self):
        with my_semaphores:
            self.markInMemcache()
            logger.error("runImageTaskThread start proces %s - %s " % (self.tid, str(my_semaphores)))
            try:
                done_1 = False
                done_2 = False
                if self.createvm() == True:
                    done_1 = True
                    if self.runvm() == True:
                        done_2 = True
            except Exception as e:
                logger.error("runImageTask Exception Error Message : %s" % str(e))

            time.sleep(my_pboot_delay)
        logger.error("runImageTaskThread stop  proces %s - %s" % (self.tid, str(my_semaphores)))


class StopImageTaskThread(multiprocessing.Process):
    def __init__(self, tid, runtime_option):
        multiprocessing.Process.__init__(self)
        self.tid = tid
        self.runtime_option = json.loads(runtime_option)

    def run(self):
        process_stop_cmd(self.tid, self.runtime_option)

class DeleteImageTaskThread(multiprocessing.Process):
    def __init__(self, tid, runtime_option):
        multiprocessing.Process.__init__(self)
        self.tid = tid
        try:
            self.runtime_option = json.loads(runtime_option)
        except Exception as e:
            logger.error("DeleteImageTaskThread load runtime_option=%s error" % runtime_option)
            self.runtime_option =''

    def run(self):
        process_delete_cmd(self.tid, self.runtime_option)
        # need to update nc's status at once
        update_nc_running_status()

class rebootPoweroffHandleTaskThread(multiprocessing.Process):
    def __init__(self, ):
        multiprocessing.Process.__init__(self)

    def handle_reboot_and_poweroff(self):
        vms = os.listdir('/storage/VMs/')
        vms = getNotRunningVMs(vms)
        for insid in vms:
            nc_ndp_stop_handle(insid, "")

    def run(self):
        self.handle_reboot_and_poweroff()

class ndpStopHandleThread(multiprocessing.Process):
    def __init__(self, insid, runtime_option):
        multiprocessing.Process.__init__(self)
        self.insid = insid
        self.runtime_option = runtime_option

    def run(self):
        ccip = getccipbyconf()
        payload = {
            'type': 'taskstatus',
            'phase': "editing",
            'state': 'ndpstopped',
            'tid': "%s:%s:%s" % (self.insid, self.insid, self.insid),
            'insid': self.insid,
            'errormsg': '',
            'failed': 0,
            'ccip': ccip,
            'ncip': getHostNetInfo()['ip0'],
        }
        safe_update_task_status(ccip, "cc", payload)

def update_nc_running_status(external=None):
    payload = { }
    payload['type']             = 'nodestatus'
    payload['service_data']     = getServiceStatus('nc')
    payload['hardware_data']    = getHostHardware()
    payload['net_data']         = getHostNetInfo()
    payload['vm_data']          = getVMlist()

    payload['nid']              = "nc#" + payload['net_data']['mac0'] + "#status"

    if external != None:
        payload['external'] = external

    ccip = getccipbyconf()
    simple_send(logger, ccip, 'cc_status_queue', json.dumps(payload))
    logger.error("update_nc_running_status hardware data %s" % json.dumps(payload['hardware_data']))

def process_stop_cmd(tid, runtime_option):
    retval   = tid.split(':')
    srcimgid = retval[0]
    dstimgid = retval[1]
    insid    = retval[2]

    with delete_semaphor:
        if len(runtime_option) > 0:
            if runtime_option['protocol'] == 'NDP':
                cmd = "pkill -f %s" % insid
            else:
                cmd = VBOX_MGR_CMD + " controlvm %s poweroff " % insid
            out = commands.getoutput(cmd)
            logger.error("Step 1 of 2: cmd=%s; result=%s" % (cmd, out))
            time.sleep(2)
        payload = {
                'type'      : 'taskstatus',
                'phase'     : "editing",
                'state'     : 'stopped',
                'progress'  : 0,
                'tid'       : tid,
                'errormsg'  : '',
                'failed'    : 0
        }
        ccip = getccipbyconf()
        # process for different type instance
        if srcimgid != dstimgid:
            rootdir = "/storage/tmp"
        else:
            rootdir = "/storage"
        vboxmgr = vboxWrapper(dstimgid, insid, rootdir)
        # build/modify insid is TMPxxxxx, when stopped, do nothing else
        if insid.find('TMP') == 0 or insid.find('PVD') == 0:
            pass
        # running vd   insid is VDxxxx,   when stopped, delete all except image file
        if insid.find('VD') == 0 or insid.find('TVD') == 0:
            # restore snapshot
            if vboxmgr.isSnapshotExist('thomas'):
                vboxmgr.restore_snapshot('thomas')
                logger.error('zmq:restore snapshot thomas for %s' % insid)
        # running vs   insid is VSxxxx,   when stopped, delete all except image file
        if insid.find('VS') == 0:
            # restore snapshot
            if vboxmgr.isSnapshotExist('thomas'):
                vboxmgr.restore_snapshot('thomas')
                logger.error('zmq:restore snapshot thomas for %s' % insid)

        logger.error("Step 2 of 2: restore snapshot of %s " % insid)
        # safe_update_task_status(ccip, "cc", payload)

def process_delete_cmd(tid, runtime_option):
    logger.error("Step 1: stop the VM when delete task of %s" % tid)
    process_stop_cmd(tid, runtime_option)

    ccip = getccipbyconf()
    payload = {
            'type'      : 'taskstatus',
            'phase'     : "editing",
            'state'     : 'deleted',
            'progress'  : 0,
            'tid'       : tid,
            'errormsg'  : '',
            'failed'    : 0
    }

    retval   = tid.split(':')
    srcimgid = retval[0]
    dstimgid = retval[1]
    insid    = retval[2]

    # process for different type instance
    rootdir = "/storage"
    if srcimgid != dstimgid:
        rootdir = "/storage/tmp"

    with delete_semaphor:
        vboxmgr = vboxWrapper(dstimgid, insid, rootdir)
        logger.error("Step 2: unregisterVM of %s" % tid)
        ret = vboxmgr.unregisterVM()
        logger.error("--- vboxmgr.unregisterVM ret=%s" % (ret))
        logger.error("Step 3: deleteVMConfigFile of %s" % tid)
        ret = vboxmgr.deleteVMConfigFile()
        logger.error("--- vboxmgr.deleteVMConfigFile ret=%s" % (ret))
        hdds = get_vm_hdds()
        disks = []
        if insid.find('TMP') == 0:
            if srcimgid != dstimgid:
                disks.append('/storage/tmp/images/%s/machine' % dstimgid)
        if insid.find('VD') == 0 or insid.find('TVD') == 0 or insid.find('PVD') == 0:
            pass
        if insid.find('VS') == 0:
            pass
        for disk in disks:
            if disk in hdds:
                cmd = VBOX_MGR_CMD + " closemedium disk %s --delete" % disk
                out = commands.getoutput(cmd)
                logger.error("cmd = %s, rsult=%s", (cmd, out))
            if os.path.exists(os.path.dirname(disk)):
                shutil.rmtree(os.path.dirname(disk))
                if os.path.exists(os.path.dirname(disk)):
                    logger.error("%s is not really deleted." % disk)
        # safe_update_task_status(ccip, "cc", payload)

#################################################
#  cmd handle function

def nc_image_prepare_handle(tid, runtime_option):
    logger.error("--- --- ---zmq: nc_image_prepare_handle for %s" % tid)
    worker = prepareImageTaskThread(tid, runtime_option)
    worker.start()
    return worker

def nc_image_run_handle(tid, runtime_option):
    recoverCrashedVMs()

    logger.error("--- --- ---zmq: nc_image_run_handle %s " % tid)
    worker = runImageTaskThread(tid, runtime_option)
    worker.start()

def nc_image_submit_handle(tid, runtime_option):
    logger.error("--- --- ---zmq: nc_image_submit_handle %s " % tid)
    worker = SubmitImageTaskThread(tid, runtime_option)
    worker.start()
    return worker

def nc_image_stop_handle(tid, runtime_option):
    logger.error("--- --- ---zmq: nc_image_stop_handle %s " % tid)
    worker = StopImageTaskThread(tid, runtime_option)
    worker.start()
    return worker

def nc_task_delete_handle(tid, runtime_option):
    logger.error("--- --- ---zmq: nc_image_delete_handle %s " % tid)
    worker = DeleteImageTaskThread(tid, runtime_option)
    worker.start()
    return worker

def nc_ndp_stop_handle(insid, runtime_option):
    logger.error("--- --- ---zmq: nc_ndp_stop_handle %s " % insid)
    worker = ndpStopHandleThread(insid, runtime_option)
    worker.start()
    return worker

def safe_update_task_status(ip, role, status_payload):
    retry = 0
    flag  = False
    url = "http://%s/%s/task/status/update" % (ip, role)
    payload = {
        "taskstatus" : json.dumps(status_payload)
    }
    while retry < 10 and not flag:
        try:
            r = requests.post(url, data=payload, timeout=None)
            if r.status_code == 200:
                logger.error("safe_update_task_status url=%s with 200 status code and payload %s" % (url, json.dumps(status_payload, indent=4)))
                flag = True
                continue
            else:
                logger.error("safe_update_task_status url=%s failed with status_code = %d and payload = %s" % (url, r.status_code, json.dumps(status_payload, indent=4)))
                logger.error("safe_update_task_status r.content=%s" % r.content)
            retry = retry + 1
            time.sleep(5)
        except Exception as e:
            logger.error("safe_update_task_status try %d time and get exception = %s" % (retry, str(e)))
            retry = retry + 1
            time.sleep(5)

    if flag == False:
        logger.error("safe_update_task_status retry %d time and failed to update task status." % retry)


nc_cmd_handlers = {
    'image/prepare'     : nc_image_prepare_handle,
    'image/run'         : nc_image_run_handle,
    'image/stop'        : nc_image_stop_handle,
    'image/submit'      : nc_image_submit_handle,
    'task/delete'       : nc_task_delete_handle,
    'ndp/stop'          : nc_ndp_stop_handle,
}

class nc_cmdConsumer():
    def __init__(self, port=NC_CMD_QUEUE_PORT):
        logger.error("zmq: nc_cmd_consumer start running")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % port)
        self.ret = {}

    def cmdHandle(self, body):
        logger.error("zmq: get cmd body = %s" % body)
        try:
            message = json.loads(body)
            if message.has_key('op') and message['op'] in  nc_cmd_handlers and nc_cmd_handlers[message['op']] != None:
                logger.error("doing nc_cmdConsumer.cmdHandle at %s" % str(nc_cmd_handlers[message['op']]))
                nc_cmd_handlers[message['op']](message['tid'], message['runtime_option'])
            else:
                logger.error("zmq: nc get unknown cmd : %s", body)
        except Exception as e:
            logger.error("zmq: exception =  %s" % str(e))

    def run(self):
        worker = rebootPoweroffHandleTaskThread()
        worker.start()
        while True:
            msg = self.socket.recv()
            self.socket.send('OK')
            logger.error("start nc_cmdConsumer.cmdHandle")
            self.cmdHandle(msg)
            logger.error("end   nc_cmdConsumer.cmdHandle")

def main():
    consumer = nc_cmdConsumer()
    consumer.run()


if __name__ == '__main__':
    main()
