from luhyaapi.vboxWrapper import *
import  json, time, shutil, os

class runImageTaskThread():
    def __init__(self, tid, runtime_option):
        retval = tid.split(':')
        self.tid      = tid
        self.srcimgid = retval[0]
        self.dstimgid = retval[1]
        self.insid    = retval[2]
        self.runtime_option = json.loads(runtime_option)

    def createvm(self):
        flag = False
        if self.srcimgid != self.dstimgid:
            rootdir = "/storage/tmp"
        else:
            rootdir = "/storage"

        self.vboxmgr = vboxWrapper(self.dstimgid, self.insid, rootdir)
        vboxmgr = self.vboxmgr

        # register VM
        if not vboxmgr.isVMRegistered():
            if vboxmgr.isVMRegisteredBefore():
                ret, err = vboxmgr.registerVM()
            else:
                try:
                    ostype_value = self.runtime_option['ostype']
                    ret, err = vboxmgr.createVM(ostype=ostype_value)
                    ret, err = vboxmgr.registerVM()
                    if "WindowsXP" in ostype_value or "Windows2003" in ostype_value:
                        ret, err = vboxmgr.addCtrl(" --name IDE --add ide ")
                    else:
                        ret, err = vboxmgr.addCtrl(" --name IDE --add ide ")
                        ret, err = vboxmgr.addCtrl(" --name SATA --add sata ")
                    ret, err = vboxmgr.attachHDD_c(storageCtl = self.runtime_option['storagectltype'])

                    snapshot_name = "thomas"
                    if not vboxmgr.isSnapshotExist(snapshot_name):
                        ret, err = vboxmgr.take_snapshot(snapshot_name)
                        
                    if self.runtime_option['usage'] == "desktop":
                        if "Windows" in ostype_value:
                            ret, err = vboxmgr.attachHDD_shared_d()
                        
                    # in server side, the SharedFolder is by default
                    ret, err = vboxmgr.attachSharedFolder(path="/storage/data")
                    
                    # in servere side, each VM has 4G mem
                    ostypepara_value = self.runtime_option['network']  +  self.runtime_option['waishe_para']
                    _cpus = self.runtime_option['cpus']
                    _memory  = self.runtime_option['memory']
                    ret, err = vboxmgr.modifyVM(osTypeparam=ostypepara_value, cpus = _cpus, mem=_memory, )

                    # in server side, configure headless property
                    portNum = 3301 # getUnusedPort(dID)
                    ret, err = vboxmgr.addHeadlessProperty(port=portNum)
                except:
                    ret, err = vboxmgr.unregisterVM()
                    vboxmgr.deleteVMConfigFile()
                    return

                ret, err = vboxmgr.unregisterVM()
                ret, err = vboxmgr.registerVM()
        


runtime_option = {}

# for xp,and w2003, only on CTRL
# runtime_option['usage']   = "desktop"
# runtime_option['memory']  = 2048
# runtime_option['cpus']    = 1
# runtime_option['ostype']  = "WindowsXP"
# runtime_option['network'] = " --nic1 nat  --nictype1 Am79C973 "
# runtime_option['storagectltype'] =  "IDE"
# runtime_option['waishe_para'] = " --audio coreaudio --audiocontroller ac97 "

# for win7
runtime_option['usage']   = "desktop"
runtime_option['memory']  = 2048
runtime_option['cpus']    = 1
runtime_option['ostype']  = "Windows7"
runtime_option['network'] = " --nic1 bridged --bridgeadapter1 en0 --nictype1 82540EM "
runtime_option['storagectltype'] =  "SATA"
runtime_option['storagectl'] = " --name SATA --add sata"
runtime_option['waishe_para'] = "--audio coreaudio --audiocontroller hda"

# for ubuntu
# runtime_option['usage']   = "desktop"
# runtime_option['memory']  = 2048
# runtime_option['cpus']    = 1
# runtime_option['ostype']  = "Ubuntu_64"
# runtime_option['network'] = " --nic1 bridged --bridgeadapter1 en0 --nictype1 82540EM "
# runtime_option['storagectltype'] =  "SATA"
# runtime_option['storagectl'] = " --name SATA --add sata "
# runtime_option['waishe_para'] = " --audio coreaudio --audiocontroller ac97  "


obj = runImageTaskThread("imgtest:win7:TMPINS1234", json.dumps(runtime_option))
obj.createvm()
